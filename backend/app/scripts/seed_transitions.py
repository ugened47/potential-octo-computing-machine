"""Seed database with built-in transitions and effects."""

import asyncio
from uuid import uuid4

from app.core.db import async_session_maker
from app.models import CompositionEffect, EffectType, Transition, TransitionType


async def seed_transitions() -> None:
    """Seed database with built-in transitions."""
    async with async_session_maker() as db:
        # Check if transitions already exist
        from sqlmodel import select

        result = await db.execute(select(Transition).where(Transition.is_builtin == True))
        existing = result.scalars().all()

        if existing:
            print(f"Found {len(existing)} existing built-in transitions. Skipping seed.")
            return

        # Define built-in transitions
        transitions = [
            Transition(
                id=uuid4(),
                name="Fade",
                transition_type=TransitionType.FADE,
                default_duration=0.5,
                parameters={"easing": "linear"},
                is_builtin=True,
                is_public=True,
            ),
            Transition(
                id=uuid4(),
                name="Dissolve",
                transition_type=TransitionType.DISSOLVE,
                default_duration=1.0,
                parameters={"easing": "ease-in-out"},
                is_builtin=True,
                is_public=True,
            ),
            Transition(
                id=uuid4(),
                name="Slide Left",
                transition_type=TransitionType.SLIDE,
                default_duration=0.75,
                parameters={"direction": "left", "easing": "ease-out"},
                is_builtin=True,
                is_public=True,
            ),
            Transition(
                id=uuid4(),
                name="Slide Right",
                transition_type=TransitionType.SLIDE,
                default_duration=0.75,
                parameters={"direction": "right", "easing": "ease-out"},
                is_builtin=True,
                is_public=True,
            ),
            Transition(
                id=uuid4(),
                name="Wipe Horizontal",
                transition_type=TransitionType.WIPE,
                default_duration=1.0,
                parameters={"direction": "horizontal", "easing": "linear"},
                is_builtin=True,
                is_public=True,
            ),
            Transition(
                id=uuid4(),
                name="Wipe Vertical",
                transition_type=TransitionType.WIPE,
                default_duration=1.0,
                parameters={"direction": "vertical", "easing": "linear"},
                is_builtin=True,
                is_public=True,
            ),
            Transition(
                id=uuid4(),
                name="Zoom In",
                transition_type=TransitionType.ZOOM,
                default_duration=0.5,
                parameters={"direction": "in", "easing": "ease-in"},
                is_builtin=True,
                is_public=True,
            ),
            Transition(
                id=uuid4(),
                name="Zoom Out",
                transition_type=TransitionType.ZOOM,
                default_duration=0.5,
                parameters={"direction": "out", "easing": "ease-out"},
                is_builtin=True,
                is_public=True,
            ),
            Transition(
                id=uuid4(),
                name="Blur Transition",
                transition_type=TransitionType.BLUR,
                default_duration=0.75,
                parameters={"max_blur": 20, "easing": "ease-in-out"},
                is_builtin=True,
                is_public=True,
            ),
        ]

        # Add transitions to database
        for transition in transitions:
            db.add(transition)

        await db.commit()
        print(f"Seeded {len(transitions)} built-in transitions")


async def seed_effects() -> None:
    """Seed database with built-in composition effects."""
    async with async_session_maker() as db:
        # Check if effects already exist
        from sqlmodel import select

        result = await db.execute(
            select(CompositionEffect).where(CompositionEffect.is_builtin == True)
        )
        existing = result.scalars().all()

        if existing:
            print(f"Found {len(existing)} existing built-in effects. Skipping seed.")
            return

        # Define built-in effects
        effects = [
            CompositionEffect(
                id=uuid4(),
                name="Grayscale",
                effect_type=EffectType.FILTER,
                parameters={"saturation": 0},
                ffmpeg_filter="hue=s=0",
                is_builtin=True,
            ),
            CompositionEffect(
                id=uuid4(),
                name="Sepia",
                effect_type=EffectType.COLOR,
                parameters={"red": 1.2, "green": 1.0, "blue": 0.8},
                ffmpeg_filter="colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
                is_builtin=True,
            ),
            CompositionEffect(
                id=uuid4(),
                name="Brightness +20%",
                effect_type=EffectType.COLOR,
                parameters={"brightness": 0.2},
                ffmpeg_filter="eq=brightness=0.2",
                is_builtin=True,
            ),
            CompositionEffect(
                id=uuid4(),
                name="Contrast +20%",
                effect_type=EffectType.COLOR,
                parameters={"contrast": 1.2},
                ffmpeg_filter="eq=contrast=1.2",
                is_builtin=True,
            ),
            CompositionEffect(
                id=uuid4(),
                name="Saturation +30%",
                effect_type=EffectType.COLOR,
                parameters={"saturation": 1.3},
                ffmpeg_filter="eq=saturation=1.3",
                is_builtin=True,
            ),
            CompositionEffect(
                id=uuid4(),
                name="Blur (Light)",
                effect_type=EffectType.BLUR,
                parameters={"radius": 5},
                ffmpeg_filter="boxblur=5:1",
                is_builtin=True,
            ),
            CompositionEffect(
                id=uuid4(),
                name="Sharpen",
                effect_type=EffectType.SHARPEN,
                parameters={"amount": 1.5},
                ffmpeg_filter="unsharp=5:5:1.5:5:5:0.0",
                is_builtin=True,
            ),
        ]

        # Add effects to database
        for effect in effects:
            db.add(effect)

        await db.commit()
        print(f"Seeded {len(effects)} built-in effects")


async def main() -> None:
    """Main seed function."""
    print("Seeding database with built-in transitions and effects...")
    await seed_transitions()
    await seed_effects()
    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
