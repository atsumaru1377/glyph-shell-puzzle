"""重なった字を切り分ける接触面を決め、ピースの形を頂点の上の値として作る。

2つの字が重なった所は、両方の輪郭から等しい距離の線で切り分ける。その切り口が接触面で、
字の輪郭の内側にある。接触面の両側には、磁石の穴とそのまわりの壁が入る大きさの四角い台を
足す。字が重なっている所に置くので、台の大部分は字の輪郭の内側に収まり、字が細い所や
丸い所でだけ、角が少しはみ出す。
"""

from dataclasses import dataclass

import numpy as np

from glyphshell.layout import Placement
from glyphshell.surface import Surface

# 値を見積もるのに使う頂点の範囲（見たい点からの距離）。
# メッシュの辺の長さ 1.4 mm の約2倍で、まわりの頂点が十数個入る。
FIT_RADIUS = 3.0
# 切り口の幅を測るときの刻み。メッシュの辺の長さより十分細かくする。
WIDTH_STEP = 0.2
# 切り口の幅を測る範囲（中心から片側）。接触面に要る幅の数倍あればよい。
WIDTH_RANGE = 20.0


@dataclass(frozen=True)
class PadSize:
    length: float  # 接触面に垂直な向きの長さ（両側の合計）
    width: float  # 接触面に沿った幅
    # 台の大きさを測る高さ（曲面から法線の外向きに）。磁石の穴は曲面から離れた所に開くので、
    # 曲面が曲がっていると、曲面の上で測った台とは大きさが変わる。0 なら曲面の上で測る
    lift: float = 0.0


@dataclass(frozen=True)
class Contact:
    a: int  # ピースの番号（a < b）
    b: int
    point: np.ndarray  # 接触面の中心（曲面の上）
    normal: np.ndarray  # その点での曲面の外向きの法線
    direction: np.ndarray  # a から b へ向かう向き（接触面の法線。曲面に接する）
    width: float  # 切り口の幅


def dense_fields(placements: list[Placement], vertex_count: int) -> np.ndarray:
    """[ピース, 頂点] の符号付き距離。値を持たない頂点は無限大。"""
    fields = np.full((len(placements), vertex_count), np.inf)
    for i, placement in enumerate(placements):
        fields[i, placement.index] = placement.distance
    return fields


def _fit(positions: np.ndarray, values: np.ndarray, normal: np.ndarray, point: np.ndarray):
    """point のまわりの頂点の値に平面を当てはめ、(point での値, 曲面に沿った勾配) を返す。"""
    steps = positions - point
    steps = steps - np.outer(steps @ normal, normal)
    design = np.hstack([np.ones((len(steps), 1)), steps])
    solution, *_ = np.linalg.lstsq(design, values, rcond=None)
    gradient = solution[1:] - (solution[1:] @ normal) * normal
    return float(solution[0]), gradient


def _clusters(positions: np.ndarray, link: float) -> list[np.ndarray]:
    """点を、link より近いものどうしでつないだまとまりに分ける。"""
    remaining = np.ones(len(positions), dtype=bool)
    groups = []
    while remaining.any():
        group = [int(np.flatnonzero(remaining)[0])]
        remaining[group[0]] = False
        for k in group:
            close = remaining & (np.linalg.norm(positions - positions[k], axis=1) < link)
            group.extend(np.flatnonzero(close).tolist())
            remaining[close] = False
        groups.append(np.array(group))
    return groups


def _pad_coordinates(surface: Surface, contact: Contact, pad: PadSize):
    """台のまわりの頂点について、(頂点の番号, 接触面からの距離 s, 面に沿った位置 t) を返す。"""
    offset = (surface.vertices + pad.lift * surface.normals) - (contact.point + pad.lift * contact.normal)
    # 同じ側の面だけを対象にする（薄い形の裏側を拾わない）
    near = (np.linalg.norm(offset, axis=1) < np.hypot(pad.length, pad.width)) & (
        surface.normals @ contact.normal > 0.5
    )
    index = np.flatnonzero(near)
    along = offset[index] @ contact.direction
    across = offset[index] @ np.cross(contact.normal, contact.direction)
    return index, along, across


def _pad_box(along: np.ndarray, across: np.ndarray, pad: PadSize) -> np.ndarray:
    """台の四角形の内側で負になる値。"""
    return np.maximum(np.abs(along) - pad.length / 2, np.abs(across) - pad.width / 2)


def find_contacts(
    surface: Surface, placements: list[Placement], min_width: float, pad: PadSize
) -> list[Contact]:
    """2つの字が重なった所のうち、切り口の幅が min_width 以上の所を接触として返す。

    切り口の幅が広い順に採用する。台が3つ目の字や、先に採用した台にかかる接触は採用しない。
    """
    fields = dense_fields(placements, len(surface.vertices))
    edges = surface.vertices[surface.faces[:, 0]] - surface.vertices[surface.faces[:, 1]]
    link = 2 * float(np.linalg.norm(edges, axis=1).mean())
    contacts = []
    for a in range(len(placements)):
        for b in range(a + 1, len(placements)):
            both = np.flatnonzero(np.isfinite(fields[a]) & np.isfinite(fields[b]))
            lens = both[(fields[a, both] < 0) & (fields[b, both] < 0)]
            if len(lens) == 0:
                continue
            positions = surface.vertices[both]
            for group in _clusters(surface.vertices[lens], link):
                members = lens[group]
                deepest = members[np.maximum(fields[a, members], fields[b, members]).argmin()]
                normal = surface.normals[deepest]
                point = surface.vertices[deepest]
                # 切り口の線は (a までの距離 − b までの距離) が 0 の所。a から b へ向かうと増える
                side = (fields[a, both] - fields[b, both]) / 2
                around = np.linalg.norm(positions - point, axis=1) < FIT_RADIUS
                value, gradient = _fit(positions[around], side[around], normal, point)
                length = np.linalg.norm(gradient)
                if length < 0.5:  # 正しく見積もれていれば 1 に近い
                    continue
                direction = gradient / length
                point = point - direction * value / length
                tangent = np.cross(normal, direction)
                # 切り口に沿って、両方の字の内側である範囲を測る
                steps = np.arange(-WIDTH_RANGE, WIDTH_RANGE + WIDTH_STEP, WIDTH_STEP)
                inside = np.zeros(len(steps), dtype=bool)
                for k, t in enumerate(steps):
                    sample = point + t * tangent
                    close = np.linalg.norm(positions - sample, axis=1) < FIT_RADIUS
                    if close.sum() >= 4:
                        # 距離は字ごとに当てはめる。2つの大きいほうは切り口で折れるので、
                        # まとめて平面を当てはめると内側を外側と見誤る
                        inside[k] = all(
                            _fit(positions[close], fields[piece, both][close], normal, sample)[0] < 0
                            for piece in (a, b)
                        )
                middle = len(steps) // 2
                if not inside[middle]:
                    continue
                first = middle - int(np.argmin(inside[middle::-1])) + 1 if not inside[: middle + 1].all() else 0
                last = middle + int(np.argmin(inside[middle:])) - 1 if not inside[middle:].all() else len(steps) - 1
                width = float(steps[last] - steps[first])
                if width < min_width:
                    continue
                centre = point + (steps[first] + steps[last]) / 2 * tangent
                # 中心を動かしたので、法線をその場所で取り直し、中心を曲面の上へ戻す。
                # 接触面は法線を含む平面にする。そうしないと、法線に沿って作るピースの壁が
                # 厚みの奥で平面から離れる
                close = np.linalg.norm(positions - centre, axis=1) < FIT_RADIUS
                here = np.array(
                    [_fit(positions[close], surface.normals[both][close][:, k], normal, centre)[0] for k in range(3)]
                )
                here /= np.linalg.norm(here)
                anchor = positions[np.linalg.norm(positions - centre, axis=1).argmin()]
                centre = centre - ((centre - anchor) @ here) * here
                facing = direction - (direction @ here) * here
                contacts.append(Contact(a, b, centre, here, facing / np.linalg.norm(facing), width))
    contacts.sort(key=lambda contact: -contact.width)

    accepted: list[Contact] = []
    taken = np.zeros(len(surface.vertices), dtype=bool)
    for contact in contacts:
        index, along, across = _pad_coordinates(surface, contact, pad)
        inside_pad = index[_pad_box(along, across, pad) < 0]
        others = np.delete(fields[:, inside_pad], [contact.a, contact.b], axis=0)
        if (others.size and others.min() < 0) or taken[inside_pad].any():
            continue
        taken[inside_pad] = True
        accepted.append(contact)
    return accepted


def stable_pieces(piece_count: int, contacts: list[Contact], minimum: int) -> list[int]:
    """接触が minimum か所に届かないピースを外していき、残ったピースの番号を返す。

    外したピースとの接触も無くなるので、届かないピースが無くなるまで繰り返す。
    """
    kept = set(range(piece_count))
    while True:
        counts = dict.fromkeys(kept, 0)
        for contact in contacts:
            if contact.a in kept and contact.b in kept:
                counts[contact.a] += 1
                counts[contact.b] += 1
        short = {piece for piece, count in counts.items() if count < minimum}
        if not short:
            return sorted(kept)
        kept -= short


def connected_pieces(piece_count: int, contacts: list[Contact], minimum: int) -> list[int]:
    """接触が minimum か所以上あるピースの番号を返す。stable_pieces と違い、外した先の連鎖はさせない。

    字を入れ直すときの足場に使う。連鎖させると、1つ足りないだけの字から全部が外れることがある。
    """
    counts = np.zeros(piece_count, dtype=int)
    for contact in contacts:
        counts[contact.a] += 1
        counts[contact.b] += 1
    return np.flatnonzero(counts >= minimum).tolist()


def piece_fields(
    surface: Surface, placements: list[Placement], contacts: list[Contact], pad: PadSize
) -> np.ndarray:
    """[ピース, 頂点] の値を返す。負の頂点がそのピースの内側。

    ピースは、字に接触の台の半分を足し、ほかのピースのほうが近い所（重なりの向こう半分）を
    取り除いた形。台の中では、接触面の平面で両側のピースを分ける。どの頂点も、内側になるピースは多くても1つ。辺の上で値を直線で補間しても、
    2つのピースの内側は重ならない。
    """
    raw = dense_fields(placements, len(surface.vertices))
    for contact in contacts:
        index, along, across = _pad_coordinates(surface, contact, pad)
        box = _pad_box(along, across, pad)
        for piece, side in ((contact.a, along), (contact.b, -along)):
            half = np.maximum(box, side)
            # 台の中は、接触面（平面）だけで両側を分ける。字の輪郭から等しい距離の線は平面から
            # 少しずれるので、台の中でもそれを使うと、磁石の穴の口が壁の面とそろわない
            raw[piece, index] = np.where(box < 0, half, np.minimum(raw[piece, index], half))
    order = np.argsort(raw, axis=0)[:2]
    lowest = np.take_along_axis(raw, order[:1], axis=0)[0]
    second = np.take_along_axis(raw, order[1:2], axis=0)[0]
    others = np.where(np.arange(len(raw))[:, None] == order[0][None, :], second, lowest)
    # ほかのピースとの境は (自分の値 − 相手の値) / 2 が 0 の所。2 で割るのは、境の両側で値の
    # 傾きをそろえるため。割らないと、辺の上で 0 になる点が境より手前にずれて隙間ができる
    with np.errstate(invalid="ignore"):
        trimmed = np.maximum(raw, (raw - others) / 2)
    return np.where(np.isfinite(raw), trimmed, np.inf)
