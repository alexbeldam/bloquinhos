class GravityController:
    @staticmethod
    def calculate_gravity_interval(level: int) -> float:
        from settings import SETTINGS

        difficulty = SETTINGS.DIFFICULTY
        fall_speed_ms = max(
            difficulty.MIN_FALL_SPEED,
            difficulty.INITIAL_FALL_SPEED
            * (difficulty.SPEED_DECREMENT_RATIO ** (level - 1)),
        )

        return fall_speed_ms / 1000
