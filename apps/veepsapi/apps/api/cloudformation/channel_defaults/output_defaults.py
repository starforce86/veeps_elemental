from troposphere import medialive

output2160p = medialive.Output(
    AudioDescriptionNames=["audio_1", "audio_1eac3"],
    OutputName="2160p30",
    OutputSettings=medialive.OutputSettings(
        MediaPackageOutputSettings=medialive.MediaPackageOutputSettings(),
    ),
    VideoDescriptionName="2160p30",
)

output1080p = medialive.Output(
    AudioDescriptionNames=["audio_1", "audio_2eac3"],
    OutputName="1080p30",
    OutputSettings=medialive.OutputSettings(
        MediaPackageOutputSettings=medialive.MediaPackageOutputSettings(),
    ),
    VideoDescriptionName="video_1080p30",
)
output720p = medialive.Output(
    AudioDescriptionNames=["audio_2", "audio_2eac3"],
    OutputName="720p30",
    OutputSettings=medialive.OutputSettings(
        MediaPackageOutputSettings=medialive.MediaPackageOutputSettings(),
    ),
    VideoDescriptionName="video_720p30",
)
output480p = medialive.Output(
    AudioDescriptionNames=["audio_3", "audio_2eac3"],
    OutputName="480p30",
    OutputSettings=medialive.OutputSettings(
        MediaPackageOutputSettings=medialive.MediaPackageOutputSettings(),
    ),
    VideoDescriptionName="video_480p30",
)
output240p = medialive.Output(
    AudioDescriptionNames=["audio_4", "audio_2eac3"],
    OutputName="240p30",
    OutputSettings=medialive.OutputSettings(
        MediaPackageOutputSettings=medialive.MediaPackageOutputSettings(),
    ),
    VideoDescriptionName="video_240p30",
)

output_preview = medialive.Output(
    AudioDescriptionNames=["audio_preview"],
    OutputName="video_240p30preview",
    OutputSettings=medialive.OutputSettings(
        MediaPackageOutputSettings=medialive.MediaPackageOutputSettings(),
    ),
    VideoDescriptionName="video_240p30preview",
)

mediastore_output1080p = medialive.Output(
    AudioDescriptionNames=["audio_1", "audio_2eac3"],
    OutputName="mediastore1080p30",
    OutputSettings=medialive.OutputSettings(
        HlsOutputSettings=medialive.HlsOutputSettings(
            HlsSettings=medialive.HlsSettings(
                StandardHlsSettings=medialive.StandardHlsSettings(
                    M3u8Settings=medialive.M3u8Settings(
                        AudioFramesPerPes=4,
                        AudioPids="492-498",
                        NielsenId3Behavior="NO_PASSTHROUGH",
                        PcrControl="PCR_EVERY_PES_PACKET",
                        PmtPid="480",
                        ProgramNum=1,
                        Scte35Pid="500",
                        Scte35Behavior="NO_PASSTHROUGH",
                        TimedMetadataPid="502",
                        TimedMetadataBehavior="NO_PASSTHROUGH",
                        VideoPid="481",
                    ),
                    AudioRenditionSets="program_audio",
                ),
            ),
        ),
    ),
    VideoDescriptionName="mediastore1080p30",
)

mediastore_output2160p = medialive.Output(
    AudioDescriptionNames=["audio_1", "audio_1eac3"],
    OutputName="mediastore2160p30",
    OutputSettings=medialive.OutputSettings(
        HlsOutputSettings=medialive.HlsOutputSettings(
            HlsSettings=medialive.HlsSettings(
                StandardHlsSettings=medialive.StandardHlsSettings(
                    M3u8Settings=medialive.M3u8Settings(
                        AudioFramesPerPes=4,
                        AudioPids="492-498",
                        NielsenId3Behavior="NO_PASSTHROUGH",
                        PcrControl="PCR_EVERY_PES_PACKET",
                        PmtPid="480",
                        ProgramNum=1,
                        Scte35Pid="500",
                        Scte35Behavior="NO_PASSTHROUGH",
                        TimedMetadataPid="502",
                        TimedMetadataBehavior="NO_PASSTHROUGH",
                        VideoPid="481",
                    ),
                    AudioRenditionSets="program_audio",
                ),
            ),
        ),
    ),
    VideoDescriptionName="mediastore2160p30",
)
