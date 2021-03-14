# MicroPython esp32 AEHA 赤外線リモコン送信
import time

T = 436
HEADER_HIGH_US = 3400
HEADER_LOW_US = 1750


def reverce_8bit(data_8bit: int) -> int:
    """8bit を反転させる

    Parameters
    ----------
    data_8bit : int
        8bit数値

    Returns
    -------
    int
        ビット反転後の数値
    """

    data_8bit = ((data_8bit & 0b01010101) << 1) | ((data_8bit & 0b10101010) >> 1)
    data_8bit = ((data_8bit & 0b00110011) << 2) | ((data_8bit & 0b11001100) >> 2)
    return (data_8bit & 0b00001111) << 4 | data_8bit >> 4


def cal_parity(customer_code: list) -> int:
    """パリティ計算

    Parameters
    ----------
    customer_code : int
        カスタマーコード

    Returns
    -------
    int
        パリティ計算結果
    """
    parity = 0b0000
    for i in customer_code:
        upper_4bit = i >> 4
        lower_4bit = i & 0b00001111
        parity = parity ^ upper_4bit ^ lower_4bit
    return parity


def cal_sum(data_lsb: list) -> int:
    """チェックサム計算

    Parameters
    ----------
    data_lsb : list
        データ配列

    Returns
    -------
    int
        チェックサム値
    """
    val = 0
    for i in data_lsb:
        val = (val + i) % 256
    return val


def encode_ir_data(customer_code_lsb: list, data_lsb: list) -> str:
    """カスタマーコード、データを0, 1文字列に変換

    Parameters
    ----------
    customer_code : List[int]
        カスタマーコード
    data : List[int]
        送信データ

    Returns
    -------
    str
        0,1文字列
    """
    bit_str = ""
    customer_code_msb = [reverce_8bit(i) for i in customer_code_lsb]
    for d in customer_code_msb:
        bit_str += "{0:08b}".format(d)
    bit_str = bit_str + "{:04b}".format(cal_parity(customer_code_msb))

    data_msb = [reverce_8bit(i) for i in data_lsb]
    check_sum = cal_sum(customer_code_lsb + data_lsb)
    data_msb.append(reverce_8bit(check_sum))
    for i, d in enumerate(data_msb):
        if i == 0:
            bit_str += "{:04b}".format(d)
        else:
            bit_str += "{:08b}".format(d)
    return bit_str


def generate_frame(bit_code: str) -> list:
    """01文字列からON/OFFの時間に変換

    Parameters
    ----------
    bit_code : str
        0,1文字列

    Returns
    -------
    list
        ON/OFF時間の配列
    """
    pulse_width_data = [HEADER_HIGH_US, HEADER_LOW_US]
    for bit in bit_code:
        if bit == "0":
            pulse_width_data.extend([T, T])
        else:
            pulse_width_data.extend([T, 3 * T])
    pulse_width_data.extend([T])
    return pulse_width_data


def send_ir_data(rmt, customer_code, *data):
    if len(data) == 0:
        raise TypeError("data引数がありません")
    for d in data:
        bit_code = encode_ir_data(customer_code, d)
        frame = generate_frame(bit_code)
        rmt.write_pulses(frame, start=1)
        while not (rmt.wait_done()):
            time.sleep_us(T)
        time.sleep_us(8000)

