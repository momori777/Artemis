"""
Hormones Module - 荷尔蒙/生理周期计算

借鉴 girl-agent 的高斯周期模型，但做简化处理，适合 Python 实现。

每个角色的状态存放在 memory/role_play/<char>/relationship.json 中。
"""

import math
import random
import datetime


def _gauss(x: float, mu: float, sigma: float) -> float:
    """高斯函数。"""
    d = (x - mu) / sigma
    return math.exp(-0.5 * d * d)


def _seed_rand(seed: int, salt: int) -> float:
    """确定性随机数（基于种子）。"""
    x = math.sin(seed * 9301.13 + salt * 49297.71) * 233280
    return x - math.floor(x)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _mod(a: int, n: int) -> int:
    return ((a % n) + n) % n


def compute_hormones(
    birth_seed: int = 42,
    age: int = 18,
    now: datetime.datetime | None = None,
    stress_load: float = 0.0,
) -> dict:
    """
    计算荷尔蒙状态。

    参数:
        birth_seed: 出生随机种子（每个角色不同）
        age: 角色年龄
        now: 当前时间
        stress_load: 压力负载 0~1

    返回:
        dict 包含所有荷尔蒙和心理状态字段
    """
    if now is None:
        now = datetime.datetime.now()

    # 1) 周期长度（根据年龄）
    r = _seed_rand(birth_seed, 7)
    if age <= 18:
        cycle_length = 24 + int(r * 10)  # 24-34
    elif age <= 22:
        cycle_length = 25 + int(r * 7)   # 25-32
    else:
        cycle_length = 26 + int(r * 6)   # 26-32

    # 2) 当前周期天数
    day_of_year = now.timetuple().tm_yday
    teen_jitter = int(_seed_rand(birth_seed, day_of_year) - 0.5) * 2 if age <= 18 else 0
    stress_shift = int(stress_load * 3)
    cycle_day = _mod(day_of_year + birth_seed + teen_jitter - stress_shift, cycle_length) + 1

    # 3) 排卵日（周期长度-14）
    ovul_day = cycle_length - 14

    # 4) 周期阶段
    if cycle_day <= 4:
        phase = "menstrual"
    elif cycle_day <= ovul_day - 5:
        phase = "early-follicular"
    elif cycle_day <= ovul_day - 1:
        phase = "late-follicular"
    elif cycle_day <= ovul_day + 1:
        phase = "ovulation"
    elif cycle_day <= ovul_day + 8:
        phase = "early-luteal"
    else:
        phase = "late-luteal"

    # 5) 雌激素（双峰：排卵前主峰 + 黄体期次峰）
    estrogen = _clamp(18 + 80 * _gauss(cycle_day, ovul_day - 1, 2) + 32 * _gauss(cycle_day, ovul_day + 7, 3), 0, 100)

    # 6) 孕酮（排卵后升高）
    if cycle_day > ovul_day:
        progesterone = _clamp(85 * _gauss(cycle_day, ovul_day + 7, 3.5), 0, 100)
    else:
        progesterone = _clamp(5 * _gauss(cycle_day, ovul_day + 1, 1.5), 0, 100)

    # 7) LH（排卵日尖峰）
    lh = _clamp(95 * _gauss(cycle_day, ovul_day - 1.5, 0.6) + 8, 0, 100)

    # 8) 催产素
    oxytocin = _clamp(45 + (estrogen - 40) * 0.25, 10, 100)
    if phase == "ovulation":
        oxytocin += 18
    if phase == "late-luteal":
        oxytocin -= 8

    # 9) 皮质醇（昼夜节律 + 周期影响）
    hour = now.hour + now.minute / 60
    car_curve = math.cos(((hour - 8) / 24) * math.pi * 2)  # -1~+1, +1 at 8am
    cortisol = _clamp(
        35 + car_curve * 28 +
        (12 if phase in ("early-luteal", "late-luteal") else 0) +
        (10 if phase == "menstrual" else 0) +
        (10 if age <= 18 else 0 if age <= 22 else 0) +
        stress_load * 20,
        0, 100
    )

    # 10) PMDD (~8%概率)
    pmdd = _seed_rand(birth_seed, 13) < 0.08

    # ====== 心理状态映射 ======

    # 能量
    phase_energy = {
        "menstrual": -0.25,
        "early-follicular": 0.05,
        "late-follicular": 0.2,
        "ovulation": 0.25,
        "early-luteal": 0.0,
        "late-luteal": (-0.4 if pmdd else -0.2),
    }
    day_circ = math.sin(((hour - 6) / 24) * math.pi * 2) * 0.45
    energy = _clamp(day_circ + phase_energy.get(phase, 0) - stress_load * 0.2, -1, 1)

    # 易怒度
    phase_irrit = {
        "menstrual": 0.5,
        "early-follicular": 0.2,
        "late-follicular": 0.12,
        "ovulation": 0.08,
        "early-luteal": 0.25,
        "late-luteal": (0.85 if pmdd else 0.55),
    }
    irritability = _clamp(
        phase_irrit.get(phase, 0.2) + stress_load * 0.25 + (0.1 if age <= 18 else 0),
        0, 1
    )

    # 亲密度
    phase_aff = {
        "ovulation": 0.85,
        "late-follicular": 0.7,
        "early-follicular": 0.55,
        "early-luteal": 0.5,
        "menstrual": 0.35,
        "late-luteal": (0.2 if pmdd else 0.4),
    }
    affection = _clamp(phase_aff.get(phase, 0.5) - stress_load * 0.15, 0, 1)

    # 性欲
    libido_ovul = _gauss(cycle_day, ovul_day - 1, 2)
    libido_late = 0.35 * _gauss(cycle_day, ovul_day - 5, 4)
    libido = _clamp(libido_ovul + libido_late, 0, 1)
    if phase == "menstrual":
        libido *= 0.4
    if phase == "late-luteal":
        libido *= 0.6

    # 心情（综合指标，用于行为决策）
    mood = (affection * 0.3 + (1 - irritability) * 0.3 + energy * 0.2 + (libido if phase != "menstrual" else 0) * 0.2)

    return {
        "energy": round(energy, 3),
        "mood": round(mood, 3),
        "affection": round(affection, 3),
        "irritability": round(irritability, 3),
        "libido": round(libido, 3),
        "cycle_day": cycle_day,
        "cycle_length": cycle_length,
        "cycle_phase": phase,
        "pmdd": pmdd,
        "estrogen": round(estrogen, 1),
        "progesterone": round(progesterone, 1),
        "oxytocin": round(oxytocin, 1),
        "cortisol": round(cortisol, 1),
        "lh": round(lh, 1),
        "bbt_delta": round(0.35 * min(1, (cycle_day - ovul_day) / 2) if cycle_day > ovul_day else 0, 3),
    }


def get_hormone_status(h: dict) -> str:
    """生成荷尔蒙状态的格式化文本，用于注入prompt。"""
    lines = [
        f"周期阶段: {h['cycle_phase']} (第{h['cycle_day']}/{h['cycle_length']}天)" +
        (", PMDD" if h['pmdd'] else ""),
        f"雌激素: {h['estrogen']:.0f} | 孕酮: {h['progesterone']:.0f} | 催产素: {h['oxytocin']:.0f} | 皮质醇: {h['cortisol']:.0f}",
        f"能量: {h['energy']:.2f} | 易怒: {h['irritability']:.2f} | 亲密度: {h['affection']:.2f} | 性欲: {h['libido']:.2f}",
        f"心情: {h['mood']:.2f}",
    ]
    return "\n".join(lines)
