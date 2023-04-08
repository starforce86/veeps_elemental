RTP = "rtp"
RTP_FEC = "rtp-fec"
SRT = "srt-listener"
ZIXI_PUSH = "zixi-push"
ZIXI_PULL = "zixi-pull"
RIST = "rist"
ST2110_JPEGXS = "st2110-jpegxs"
CDI = "cdi"
FUJITSU_QOS = "fujitsu-qos"

INPUT_PROTOCOLS_CHOICES = (
    (RTP, RTP),
    (RTP_FEC, RTP_FEC),
    (SRT, SRT),
    (ZIXI_PULL, ZIXI_PULL),
    (ZIXI_PUSH, ZIXI_PUSH),
    (RIST, RIST),
    (ST2110_JPEGXS, ST2110_JPEGXS),
    (CDI, CDI),
    (FUJITSU_QOS, FUJITSU_QOS),
)

INPUT_PROTOCOLS_URI_PREFIX = {
    RTP: "rtp://",
    RTP_FEC: "rtp://",
    "srt": "srt://",
    SRT: "srt://",
    ZIXI_PUSH: "udp://",  # no documentation
    ZIXI_PULL: "udp://",  # no documentation
    RIST: "rist://",
    ST2110_JPEGXS: "st2110://",
    CDI: "cdi://",
    FUJITSU_QOS: "udp://",  # no documentation?
}

""" 
Media package channel origin endpoint startover window size: 2 hours
Used for harvesting job for clipping
"""
DISTRIBUTION_ORIGIN_ENDPOINT_STARTOVER_WINDOW = 7200

INVOKE_CALLBACK_TIMEOUT = 5
WEBHOOK_SIGNING_SECRET_PREFIX = "whsec_"
WEBHOOK_SIGNATURE_HEADER_NAME = "Veeps-Signature"
