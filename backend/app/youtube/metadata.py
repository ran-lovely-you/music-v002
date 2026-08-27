"""YouTube用メタデータ生成（STEP 12 / 14）。

タイトル案・説明文・タグ・ハッシュタグ・サムネイル用画像プロンプト・BGM紹介文を自動生成する。
医学的断定表現（「認知症が治る」「認知症を予防する」「記憶力が必ず改善する」等）は生成しない。
"""
from __future__ import annotations

from app.domain.models import GenerateRequest, Instrument, NatureSound, YoutubeMetadata
from app.domain.presets import get_preset
from app.domain.safety import sanitize_medical_claims

INSTRUMENT_JA: dict[Instrument, str] = {
    Instrument.PIANO: "ピアノ",
    Instrument.HARP: "ハープ",
    Instrument.MUSIC_BOX: "オルゴール",
    Instrument.ACOUSTIC_GUITAR: "アコースティックギター",
    Instrument.FLUTE: "フルート",
    Instrument.CLARINET: "クラリネット",
    Instrument.MARIMBA: "マリンバ",
    Instrument.SOFT_STRINGS: "柔らかなストリングス",
    Instrument.PAD: "アンビエントパッド",
    Instrument.BELL: "ベル",
    Instrument.CHIME: "チャイム",
}

NATURE_JA: dict[NatureSound, str] = {
    NatureSound.RAIN: "雨音",
    NatureSound.RIVER: "川のせせらぎ",
    NatureSound.WAVES: "波の音",
    NatureSound.FOREST: "森の音",
    NatureSound.BIRDS: "小鳥のさえずり",
    NatureSound.WIND: "そよ風",
    NatureSound.CAMPFIRE: "焚き火の音",
}

DISCLAIMER_JA = (
    "※本動画は認知機能サポート・リラックス・穏やかな生活環境づくりを目的とした音響コンテンツです。"
    "医学的な効果を保証するものではありません。"
)


def generate_youtube_metadata(req: GenerateRequest) -> YoutubeMetadata:
    preset = get_preset(req.bgm_type)
    moods = req.moods or preset.default_moods
    instruments = req.instruments or preset.default_instruments
    nature = req.nature_sounds or preset.default_nature_sounds
    minutes = req.duration_sec // 60

    instrument_ja = [INSTRUMENT_JA.get(i, i.value) for i in instruments]
    nature_ja = [NATURE_JA.get(n, n.value) for n in nature]

    title_core = preset.label_ja
    titles = [
        f"高齢者向け 癒やしの{title_core}｜心穏やかに過ごすためのリラックスBGM【{minutes}分】",
        f"【{minutes}分】{title_core}の優しいBGM｜{'・'.join(instrument_ja[:2]) if instrument_ja else '静かな音色'}で過ごす穏やかな時間",
        f"認知機能サポートBGM：{title_core}｜高齢者・介護施設向け 落ち着く音楽",
    ]
    titles = [sanitize_medical_claims(t) for t in titles]

    description_lines = [
        f"このBGMは「{title_core}」をテーマに、高齢者の方にも聴きやすいよう音響設計した"
        "認知機能サポート・リラックス用の音楽です。",
        f"使用楽器：{'、'.join(instrument_ja) if instrument_ja else 'ピアノ'}",
    ]
    if nature_ja:
        description_lines.append(f"自然音：{'、'.join(nature_ja)}")
    description_lines.append(
        "急激な音量変化や強い低音・鋭い高音を避け、長時間流していても疲れにくいよう調整しています。"
        "ご自宅、デイサービス、介護施設、就寝前のリラックスタイムなどにご活用ください。"
    )
    description_lines.append(DISCLAIMER_JA)
    description = "\n".join(sanitize_medical_claims(line) for line in description_lines)

    tags = list(
        dict.fromkeys(
            [
                "高齢者向けBGM",
                "リラックス音楽",
                "認知機能サポート",
                "穏やかな音楽",
                "介護施設BGM",
                title_core,
                *instrument_ja,
                *nature_ja,
                "睡眠導入" if req.bgm_type.value == "night" else "集中",
            ]
        )
    )

    hashtags = [f"#{t}" for t in ["高齢者向けBGM", "リラックス音楽", "癒やしBGM", title_core.replace(' ', '')]]

    thumbnail_prompt = (
        f"A gentle, warm, softly lit illustration representing '{title_core}', "
        "calm pastel colors, cozy and safe atmosphere suitable for elderly viewers, "
        "no text, no frightening elements, soothing composition"
    )

    intro_text = sanitize_medical_claims(
        f"{title_core}をテーマにした、高齢者の方向けの認知機能サポートBGMです。"
        f"{'、'.join(instrument_ja) if instrument_ja else 'ピアノ'}"
        + (f"と{'、'.join(nature_ja)}" if nature_ja else "")
        + "の優しい音色で、リラックスできる穏やかな時間をお過ごしください。"
    )

    return YoutubeMetadata(
        titles=titles,
        description=description,
        tags=tags,
        hashtags=hashtags,
        thumbnail_prompt=thumbnail_prompt,
        intro_text=intro_text,
    )
