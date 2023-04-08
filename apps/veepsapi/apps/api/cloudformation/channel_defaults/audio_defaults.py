from troposphere import medialive


audio_1 = medialive.AudioDescription(
    AudioSelectorName="Default",
    AudioTypeControl="FOLLOW_INPUT",
    CodecSettings=medialive.AudioCodecSettings(
        AacSettings=medialive.AacSettings(
            Bitrate=192000,
            CodingMode="CODING_MODE_2_0",
            InputType="NORMAL",
            Profile="LC",
            RateControlMode="CBR",
            RawFormat="NONE",
            SampleRate=48000,
            Spec="MPEG4",
        )
    ),
    LanguageCodeControl="FOLLOW_INPUT",
    Name="audio_1",
)

audio_2 = medialive.AudioDescription(
    AudioSelectorName="Default",
    AudioTypeControl="FOLLOW_INPUT",
    CodecSettings=medialive.AudioCodecSettings(
        AacSettings=medialive.AacSettings(
            Bitrate=192000,
            CodingMode="CODING_MODE_2_0",
            InputType="NORMAL",
            Profile="LC",
            RateControlMode="CBR",
            RawFormat="NONE",
            SampleRate=48000,
            Spec="MPEG4",
        )
    ),
    LanguageCodeControl="FOLLOW_INPUT",
    Name="audio_2",
)
audio_3 = medialive.AudioDescription(
    AudioSelectorName="Default",
    AudioTypeControl="FOLLOW_INPUT",
    CodecSettings=medialive.AudioCodecSettings(
        AacSettings=medialive.AacSettings(
            Bitrate=128000,
            CodingMode="CODING_MODE_2_0",
            InputType="NORMAL",
            Profile="LC",
            RateControlMode="CBR",
            RawFormat="NONE",
            SampleRate=48000,
            Spec="MPEG4",
        )
    ),
    LanguageCodeControl="FOLLOW_INPUT",
    Name="audio_3",
)

audio_4 = medialive.AudioDescription(
    AudioSelectorName="Default",
    AudioTypeControl="FOLLOW_INPUT",
    CodecSettings=medialive.AudioCodecSettings(
        AacSettings=medialive.AacSettings(
            Bitrate=128000,
            CodingMode="CODING_MODE_2_0",
            InputType="NORMAL",
            Profile="LC",
            RateControlMode="CBR",
            RawFormat="NONE",
            SampleRate=48000,
            Spec="MPEG4",
        )
    ),
    LanguageCodeControl="FOLLOW_INPUT",
    Name="audio_4",
)

audio_1eac3 = medialive.AudioDescription(
    AudioTypeControl="FOLLOW_INPUT",
    CodecSettings=medialive.AudioCodecSettings(
        Eac3Settings=medialive.Eac3Settings(
            Bitrate=448000,
            CodingMode="CODING_MODE_3_2",
            DrcLine="MUSIC_STANDARD",
            DrcRf="MUSIC_STANDARD",
        )
    ),
    LanguageCodeControl="FOLLOW_INPUT",
    Name="audio_1eac3",
)

audio_2eac3 = medialive.AudioDescription(
    AudioTypeControl="FOLLOW_INPUT",
    CodecSettings=medialive.AudioCodecSettings(
        Eac3Settings=medialive.Eac3Settings(
            Bitrate=384000,
            CodingMode="CODING_MODE_3_2",
            DrcLine="MUSIC_STANDARD",
            DrcRf="MUSIC_STANDARD",
        )
    ),
    LanguageCodeControl="FOLLOW_INPUT",
    Name="audio_2eac3",
)


audio_preview = medialive.AudioDescription(
    AudioSelectorName="Default",
    AudioTypeControl="FOLLOW_INPUT",
    CodecSettings=medialive.AudioCodecSettings(
        AacSettings=medialive.AacSettings(
            Bitrate=96000,
            CodingMode="CODING_MODE_2_0",
            InputType="NORMAL",
            Profile="LC",
            RateControlMode="CBR",
            RawFormat="NONE",
            SampleRate=48000,
            Spec="MPEG4",
        )
    ),
    LanguageCodeControl="FOLLOW_INPUT",
    Name="audio_preview",
)
