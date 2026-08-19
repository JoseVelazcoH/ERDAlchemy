"""Card geometry: sizing and spacing (px)."""

NODE_W = 218
HEADER_H = 36
FIELD_H = 21
PAD = 6
GAP_X = 60
GAP_Y = 40
MARGIN = 60.0

# Approximate glyph widths (px) used by auto_node_width to fit a card to its text.
# These track the font sizes/families in the styling submodule.
FIELD_CHAR_W = 6.2       # monospace field-name / kind-label font
HEADER_CHAR_W = 7.8      # bold header-title font
HEADER_PADDING = 24      # left + right padding around the header label
FIELD_PADDING_LEFT = 10  # left inset of the field name
FIELD_LABEL_GAP = 12     # gap between field name and kind label
FIELD_PADDING_RIGHT = 8  # right inset of the kind label
