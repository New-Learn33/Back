def build_image_prompt(
    category_hint: str,
    character_name: str,
    scene_order: int,
    dialogue: str,
    subtitle_text: str,
) -> str:
    return (
        f"webtoon style, {category_hint}, main character {character_name}, "
        f"scene {scene_order}, {subtitle_text}, emotional atmosphere, "
        f"dialogue mood: {dialogue}"
    )


def generate_three_cut_images(job_id: int, template_info: dict, scenes: list):
    images = []

    for scene in scenes:
        prompt = build_image_prompt(
            category_hint=template_info["category_hint"],
            character_name=template_info["character_name"],
            scene_order=scene["scene_order"],
            dialogue=scene["dialogue"],
            subtitle_text=scene["subtitle_text"],
        )

        # TODO:
        # 나중에 여기서 실제 이미지 생성 API(OpenAI Images / Gemini 등) 호출
        # 지금은 목업 URL만 반환
        image_url = f"https://example.com/generated/{job_id}_{scene['scene_order']}.png"

        images.append(
            {
                "scene_order": scene["scene_order"],
                "image_url": image_url,
                "prompt_used": prompt,
            }
        )

    return images