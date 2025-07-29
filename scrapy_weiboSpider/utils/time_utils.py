import time
from datetime import datetime




def to_datetime(obj):
    if isinstance(obj, str):
        for fmt in ("%Y-%m-%d %H:%M", "%a %b %d %X %z %Y"):
            try:
                return datetime.strptime(obj, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unrecognized string time format: {obj}")
    elif isinstance(obj, (int, float)):
        if obj < 1e11:  # 秒级时间戳
            return datetime.fromtimestamp(obj)
        else:  # 毫秒级时间戳
            return datetime.fromtimestamp(obj / 1000)
    elif isinstance(obj, datetime):
        return obj
    else:
        raise TypeError(f"Unsupported type: {type(obj)}")


def to_millis_timestamp(t):
    """
    转毫秒级时间戳
    :param t: %Y-%m-%d %H:%M、%a %b %d %X %z %Y、秒级时间戳、毫秒级时间戳
    :return:
    """
    dt = to_datetime(t)
    return int(dt.timestamp() * 1000)


def to_timestamp(t):
    """
    转毫秒级时间戳
    :param t: %Y-%m-%d %H:%M、%a %b %d %X %z %Y、秒级时间戳、毫秒级时间戳
    :return:
    """
    dt = to_datetime(t)
    return int(dt.timestamp())



def is_a_early_than_b(a, b, can_equal=False):
    """
    :param a: %Y-%m-%d %H:%M、%a %b %d %X %z %Y、秒级时间戳、毫秒级时间戳
    :param b:同上
    :param can_equal: a和b相同时是否返回True
    :return:
    """

    a_dt = to_datetime(a)
    b_dt = to_datetime(b)

    if can_equal:
        return a_dt <= b_dt
    else:
        return a_dt < b_dt


def format_time(t, fmt: str = "%Y-%m-%d %H:%M:%S"):
    # 转字符串，默认转 年-月-日 时:分:秒
    dt = to_datetime(t)
    return dt.strftime(fmt)


