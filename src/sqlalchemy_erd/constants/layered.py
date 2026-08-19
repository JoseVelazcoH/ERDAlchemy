"""Constants for the layered layout algorithm."""

from sqlalchemy_erd.constants.geometry import GAP_Y

BARYCENTER_SWEEPS = 4
DISCONNECTED_ROW_GAP = GAP_Y * 2  # vertical gap before the disconnected-tables row
