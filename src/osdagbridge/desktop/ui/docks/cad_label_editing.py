"""
In-place editing of painted CAD dimension labels (Task I).

The CAD widgets paint labels with QPainter, so no widget exists to click on.
`EditableLabelsMixin` records the bounding rectangle of every label while it
is painted (a per-frame *hit-test registry*), and on double-click places a
temporary QLineEdit over the label. Commit happens on Enter or focus-out;
Esc cancels. The widget never writes inputs itself: it emits
``label_value_edited(key, text)`` and the template page applies the edit
through the regular validation / solver pipeline.

Host classes must define the Qt signal ``label_value_edited = Signal(str, str)``
and call ``_reset_label_registry()`` at the start of ``paintEvent`` and
``_record_label(rect, text)`` wherever a label is painted.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QEvent, QRectF, QTimer
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QLineEdit, QToolTip

from osdagbridge.core.bridge_types.plate_girder.cad_parameter_editing import (
    classify_label,
    cad_value_to_display,
)

_EDITOR_STYLE = (
    "QLineEdit { border: 1.5px solid #90AF13; background: #ffffff;"
    " padding: 0px 3px; font: 9pt 'Arial'; }"
)


class EditableLabelsMixin:
    # Opt-in: only the template-page CAD enables editing (the same widget class
    # is reused as a read-only preview inside the Additional Inputs dialog).
    labels_editable = False
    # Optional callable -> (allowed: bool, reason: str); set by the template page.
    label_edit_guard = None

    # ── registry ──────────────────────────────────────────────────────────
    def _reset_label_registry(self):
        self._label_registry = []

    def _record_label(self, rect: QRectF, text: str):
        spec = classify_label(text)
        if spec is not None:
            self._label_registry.append((QRectF(rect), spec))

    def label_spec_at(self, pos):
        """Topmost (last painted) parameter label under `pos`, or None."""
        for rect, spec in reversed(getattr(self, "_label_registry", [])):
            if rect.adjusted(-3, -3, 3, 3).contains(pos):
                return rect, spec
        return None

    # ── interaction ───────────────────────────────────────────────────────
    def _label_hover_feedback(self, pos):
        if not self.labels_editable:
            return
        hit = self.label_spec_at(pos)
        if hit is None:
            self.unsetCursor()
            return
        _rect, spec = hit
        self.setCursor(Qt.IBeamCursor if spec.editable else Qt.ForbiddenCursor)
        tip = ("Double-click to edit " + spec.caption) if spec.editable else spec.lock_reason
        self.setToolTip(tip)

    def mouseDoubleClickEvent(self, event):
        pos = event.position() if hasattr(event, "position") else event.pos()
        hit = self.label_spec_at(pos) if self.labels_editable else None
        if hit is None:
            return super().mouseDoubleClickEvent(event)
        rect, spec = hit
        if not spec.editable:
            QToolTip.showText(self.mapToGlobal(pos.toPoint()), spec.lock_reason, self)
            return
        if callable(self.label_edit_guard):
            allowed, reason = self.label_edit_guard()
            if not allowed:
                QToolTip.showText(self.mapToGlobal(pos.toPoint()), reason, self)
                return
        self.open_label_editor(rect, spec)

    def open_label_editor(self, rect: QRectF, spec):
        self.close_label_editor(commit=False)
        current = cad_value_to_display(spec, float(self.params.get(spec.cad_param, 0.0)))
        editor = QLineEdit(self)
        editor.setObjectName("cad_label_editor")
        editor.setStyleSheet(_EDITOR_STYLE)
        validator = QDoubleValidator(0.0, 1e6, 3, editor)
        validator.setNotation(QDoubleValidator.StandardNotation)
        editor.setValidator(validator)
        editor.setText(f"{current:.0f}" if spec.unit == "mm" else f"{current:.2f}")
        editor.setToolTip(f"{spec.caption} ({spec.unit}) — Enter to apply, Esc to cancel")
        width = max(int(rect.width()), 90)
        editor.setGeometry(int(rect.x()), int(rect.y()) - 2, width, int(rect.height()) + 6)
        editor.selectAll()
        editor.installEventFilter(self)
        editor.returnPressed.connect(lambda: self.close_label_editor(commit=True))
        editor.editingFinished.connect(lambda: self.close_label_editor(commit=True))
        self._label_editor = editor
        self._label_editor_spec = spec
        editor.show()
        editor.setFocus(Qt.MouseFocusReason)

    def close_label_editor(self, commit: bool):
        editor = getattr(self, "_label_editor", None)
        if editor is None:
            return
        spec = self._label_editor_spec
        self._label_editor = None          # re-entrancy guard (returnPressed + editingFinished)
        text = editor.text()
        editor.removeEventFilter(self)
        editor.setObjectName("")         # stale editor must not be found by name
        editor.hide()
        editor.deleteLater()
        if commit:
            # Defer so the editor is gone before any modal error dialog opens.
            QTimer.singleShot(0, lambda: self.label_value_edited.emit(spec.key, text))

    def _label_editor_event_filter(self, obj, event):
        """Return True if handled. Call from the host's eventFilter."""
        if obj is getattr(self, "_label_editor", None) and event.type() == QEvent.KeyPress \
                and event.key() == Qt.Key_Escape:
            self.close_label_editor(commit=False)
            return True
        return False
