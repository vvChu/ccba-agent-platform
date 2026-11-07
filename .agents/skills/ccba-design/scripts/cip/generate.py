#!/usr/bin/env python3
"""CIP Design Generator - Generate corporate identity mockups.

Supports text-and-image generation for corporate identity deliverables.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))
from core import get_cip_brief, search

# Model options
MODELS = {
    "flash": "image-fast",
    "pro": "image-pro",
}
DEFAULT_MODEL = "flash"


def load_logo_image(logo_path):
    """Load logo image using PIL for image processing"""
    try:
        from PIL import Image
    except ImportError:
        print("Error: pillow package not installed.")
        print("Install with: pip install pillow")
        return None

    logo_path = Path(logo_path)
    if not logo_path.exists():
        print(f"Error: Logo file not found: {logo_path}")
        return None

    try:
        img = Image.open(logo_path)
        # Convert to RGB if necessary (RGB recommended for image generation)
        if img.mode in ("RGBA", "P"):
            # Create white background for transparent images
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            else:
                background.paste(img)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        return img
    except Exception as e:
        print(f"Error loading logo: {e}")
        return None


# Load environment variables
def load_env():
    """Load environment variables from .env files"""
    env_paths = [
        Path(__file__).parent.parent.parent / ".env",
        Path.home() / ".claude" / "skills" / ".env",
        Path.home() / ".claude" / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key not in os.environ:
                            os.environ[key] = value.strip("\"'")


load_env()


def _lookup_cip_metadata(deliverable, style, industry, mockup):
    deliverable_info = search(deliverable, "deliverable", 1)
    deliverable_data = (
        deliverable_info.get("results", [{}])[0] if deliverable_info.get("results") else {}
    )
    style_info = search(style or "corporate minimal", "style", 1) if style else {}
    style_data = style_info.get("results", [{}])[0] if style_info.get("results") else {}
    industry_info = search(industry or "technology", "industry", 1) if industry else {}
    industry_data = industry_info.get("results", [{}])[0] if industry_info.get("results") else {}

    mockup_context = deliverable_data.get("Mockup Context", "clean professional")
    if mockup:
        mockup_info = search(mockup, "mockup", 1)
        if mockup_info.get("results"):
            mockup_context = mockup_info["results"][0].get("Scene Description", mockup_context)
    return deliverable_data, style_data, industry_data, mockup_context


def _assemble_cip_prompt_parts(
    use_logo_image,
    deliverable_name,
    brand_name,
    description,
    style_name,
    primary_colors,
    typography,
    logo_placement,
    materials,
    finishes,
    mockup_context,
    mood,
):
    if use_logo_image:
        return [
            f"Create a professional corporate identity mockup photograph of a {deliverable_name}",
            "Use the EXACT logo from the provided image - do NOT modify or recreate the logo",
            "The logo MUST appear exactly as shown in the input image",
            f"Place the logo on the {deliverable_name} at: {logo_placement}",
            f"Brand name: '{brand_name}'",
            f"{description}" if description else "",
            f"Design style: {style_name}",
            "Color scheme matching the logo colors",
            f"Materials: {materials} with {finishes} finish",
            f"Setting: {mockup_context}",
            f"Mood: {mood}",
            "Photorealistic product photography",
            "Soft natural lighting, professional studio quality",
            "8K resolution, sharp details",
        ]
    return [
        "Professional corporate identity mockup photograph",
        f"showing {deliverable_name} for brand '{brand_name}'",
        f"{description}" if description else "",
        f"{style_name} design style",
        f"using colors {primary_colors}",
        f"{typography} typography",
        f"logo placement: {logo_placement}",
        f"{materials} materials with {finishes} finish",
        f"{mockup_context} setting",
        f"{mood} mood",
        "photorealistic product photography",
        "soft natural lighting",
        "high quality professional shot",
        "8k resolution detailed",
    ]


def build_cip_prompt(
    deliverable, brand_name, style=None, industry=None, mockup=None, use_logo_image=False
):
    """Build an optimized prompt for CIP mockup generation."""
    deliverable_data, style_data, industry_data, mockup_context = _lookup_cip_metadata(
        deliverable, style, industry, mockup
    )
    deliverable_name = deliverable_data.get("Deliverable", deliverable)
    description = deliverable_data.get("Description", "")
    logo_placement = deliverable_data.get("Logo Placement", "center")
    style_name = style_data.get("Style Name", style or "corporate")
    primary_colors = style_data.get(
        "Primary Colors", industry_data.get("Primary Colors", "#0F172A #FFFFFF")
    )
    typography = style_data.get("Typography", industry_data.get("Typography", "clean sans-serif"))
    materials = style_data.get("Materials", "premium quality")
    finishes = style_data.get("Finishes", "professional")
    mood = style_data.get("Mood", industry_data.get("Mood", "professional"))

    prompt_parts = _assemble_cip_prompt_parts(
        use_logo_image,
        deliverable_name,
        brand_name,
        description,
        style_name,
        primary_colors,
        typography,
        logo_placement,
        materials,
        finishes,
        mockup_context,
        mood,
    )
    return {
        "prompt": ", ".join([p for p in prompt_parts if p]),
        "deliverable": deliverable_name,
        "style": style_name,
        "brand": brand_name,
        "colors": primary_colors,
        "mockup_context": mockup_context,
        "logo_placement": logo_placement,
    }


def _save_generated_mockup(image_data, prompt_data, output_dir):
    output_dir = Path(output_dir or Path.cwd())
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    brand_slug = prompt_data["brand"].lower().replace(" ", "-")
    deliverable_slug = prompt_data["deliverable"].lower().replace(" ", "-")
    filepath = output_dir / f"{brand_slug}-{deliverable_slug}-{timestamp}.png"
    with open(filepath, "wb") as f:
        f.write(image_data)
    print(f"\n✅ Generated: {filepath}")
    return str(filepath)


def generate_cip_mockup(
    prompt_data, output_dir=None, model_key="flash", aspect_ratio="1:1", logo_image=None
):
    """Generate image for CIP mockup."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        import llm_adapter
    except ImportError:
        print("Error: Could not import llm_adapter.")
        return None

    prompt = prompt_data["prompt"]
    model_name = MODELS.get(model_key, MODELS[DEFAULT_MODEL])
    mode = "image-editing" if logo_image else "text-to-image"

    print(
        f"\n🎨 Generating CIP mockup ({mode}): {prompt_data['deliverable']} for {prompt_data['brand']} [{model_name}]"
    )
    if logo_image:
        print(f"   Logo: Using provided image ({logo_image.size[0]}x{logo_image.size[1]})")

    try:
        effective_prompt = f"{prompt} (incorporating brand logo)" if logo_image else prompt
        image_data = llm_adapter.generate_image(
            prompt=effective_prompt, default_model=model_name, aspect_ratio=aspect_ratio
        )
        if image_data:
            return _save_generated_mockup(image_data, prompt_data, output_dir)
        print("No image generated in response")
        return None
    except Exception as e:
        print(f"Error generating image: {e}")
        return None


def generate_cip_set(
    brand_name,
    industry,
    style=None,
    deliverables=None,
    output_dir=None,
    model_key="flash",
    logo_path=None,
    aspect_ratio="1:1",
):
    """Generate a complete CIP set for a brand."""
    logo_image = load_logo_image(logo_path) if logo_path else None
    if logo_path and not logo_image:
        print("Warning: Could not load logo, falling back to text-to-image mode")

    brief = get_cip_brief(brand_name, industry, style)
    deliverables = deliverables or [
        "business card",
        "letterhead",
        "office signage",
        "vehicle",
        "polo shirt",
    ]
    results = []
    for deliverable in deliverables:
        prompt_data = build_cip_prompt(
            deliverable=deliverable,
            brand_name=brand_name,
            style=brief.get("style", {}).get("Style Name"),
            industry=industry,
            use_logo_image=(logo_image is not None),
        )
        filepath = generate_cip_mockup(
            prompt_data,
            output_dir,
            model_key=model_key,
            aspect_ratio=aspect_ratio,
            logo_image=logo_image,
        )
        if filepath:
            results.append(
                {"deliverable": deliverable, "filepath": filepath, "prompt": prompt_data["prompt"]}
            )
    return results


def check_logo_required(brand_name, skip_prompt=False):
    """Check if logo is required and suggest logo-design skill if not provided."""
    if skip_prompt:
        return "continue"

    print(f"\n⚠️  No logo image provided for '{brand_name}'")
    print("   1. Continue without logo  2. Generate logo first  3. Exit and provide --logo")
    try:
        choice = input("   Enter choice [1/2/3] (default: 1): ").strip()
        if choice == "2":
            return "generate"
        if choice == "3":
            return "exit"
        return "continue"
    except (EOFError, KeyboardInterrupt):
        return "continue"


def _parse_cip_args():
    parser = argparse.ArgumentParser(description="Generate CIP mockups using AI image generation")
    parser.add_argument("--brand", "-b", required=True, help="Brand name")
    parser.add_argument("--logo", "-l", help="Path to brand logo image")
    parser.add_argument("--deliverable", "-d", help="Single deliverable to generate")
    parser.add_argument("--deliverables", help="Comma-separated list of deliverables")
    parser.add_argument("--industry", "-i", default="technology", help="Industry type")
    parser.add_argument("--style", "-s", help="Design style")
    parser.add_argument("--mockup", "-m", help="Mockup context")
    parser.add_argument("--set", action="store_true", help="Generate full CIP set")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--model", default="flash", choices=["flash", "pro"], help="Model key")
    parser.add_argument("--ratio", default="1:1", help="Aspect ratio (1:1, 16:9, 4:3, etc.)")
    parser.add_argument("--prompt-only", action="store_true", help="Only show prompt")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--no-logo-prompt", action="store_true", help="Skip logo prompt")
    return parser.parse_args()


def _resolve_logo_for_cli(args):
    if args.logo:
        logo_image = load_logo_image(args.logo)
        if not logo_image:
            print("Error: Could not load logo image")
            sys.exit(1)
        return logo_image
    if not args.prompt_only:
        action = check_logo_required(args.brand, skip_prompt=args.no_logo_prompt)
        if action in ("generate", "exit"):
            sys.exit(0)
    return None


def _run_cip_set_cli(args, use_logo):
    deliverables = args.deliverables.split(",") if args.deliverables else None
    if args.prompt_only:
        items = deliverables or [
            "business card",
            "letterhead",
            "office signage",
            "vehicle",
            "polo shirt",
        ]
        results = [
            build_cip_prompt(
                d, args.brand, args.style, args.industry, args.mockup, use_logo_image=use_logo
            )
            for d in items
        ]
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(f"\n{r['deliverable']}:\n{r['prompt']}\n")
        return
    results = generate_cip_set(
        args.brand,
        args.industry,
        args.style,
        deliverables,
        args.output,
        model_key=args.model,
        logo_path=args.logo,
        aspect_ratio=args.ratio,
    )
    print(
        json.dumps(results, indent=2) if args.json else f"\n✅ Generated {len(results)} CIP mockups"
    )


def main():
    args = _parse_cip_args()
    logo_image = _resolve_logo_for_cli(args)
    use_logo = logo_image is not None

    if args.set or args.deliverables:
        _run_cip_set_cli(args, use_logo)
        return

    deliverable = args.deliverable or "business card"
    prompt_data = build_cip_prompt(
        deliverable, args.brand, args.style, args.industry, args.mockup, use_logo_image=use_logo
    )
    if args.prompt_only:
        print(
            json.dumps(prompt_data, indent=2)
            if args.json
            else f"\nPrompt:\n{prompt_data['prompt']}"
        )
    else:
        filepath = generate_cip_mockup(
            prompt_data,
            args.output,
            model_key=args.model,
            aspect_ratio=args.ratio,
            logo_image=logo_image,
        )
        if args.json:
            print(json.dumps({"filepath": filepath, **prompt_data}, indent=2))


if __name__ == "__main__":
    main()
