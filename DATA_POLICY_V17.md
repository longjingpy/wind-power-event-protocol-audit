# Processed-data distribution policy

The data provider permits research use and release. The current distribution decision is to publish de-identified processed datasets rather than original provider files.

The processed replacement is available in [v0.3.0](https://github.com/longjingpy/wind-power-event-protocol-audit/releases/tag/v0.3.0): seven archives, 333 turbines and 7,548,467 regular-grid rows. The complete approximately 85 MiB ZIP was downloaded without authentication and verified against the local artifact. The former v0.2.0 release remains a non-public draft; its assets and local copies are retained. Earlier downloads cannot be recalled.

The bundle uses stable study identifiers, unitless power, turbine wind, quality flags, chronological splits and relative clocks. Original turbine names, direct location fields, absolute dates and private identity/clock maps are excluded. Month and source-clock hour remain for scientific context. The metadata, data dictionary, complete file index, licence notice and verification record accompany the bundle. These measures remove direct fields; they are not a guarantee of non-reidentification from outside information.

Original third-party data and software licences remain applicable. Authorization and distribution are separate decisions: authorization to release originals does not mean that this repository will continue to serve them.
