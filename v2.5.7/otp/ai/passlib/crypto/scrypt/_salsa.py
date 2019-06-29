

def salsa20(input):
    b0, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12, b13, b14, b15 = input
    v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15 = (
     b0, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12, b13, b14, b15)
    i = 0
    while i < 4:
        t = v0 + v12 & 4294967295L
        v4 ^= (t & 33554431) << 7 | t >> 25
        t = v4 + v0 & 4294967295L
        v8 ^= (t & 8388607) << 9 | t >> 23
        t = v8 + v4 & 4294967295L
        v12 ^= (t & 524287) << 13 | t >> 19
        t = v12 + v8 & 4294967295L
        v0 ^= (t & 16383) << 18 | t >> 14
        t = v5 + v1 & 4294967295L
        v9 ^= (t & 33554431) << 7 | t >> 25
        t = v9 + v5 & 4294967295L
        v13 ^= (t & 8388607) << 9 | t >> 23
        t = v13 + v9 & 4294967295L
        v1 ^= (t & 524287) << 13 | t >> 19
        t = v1 + v13 & 4294967295L
        v5 ^= (t & 16383) << 18 | t >> 14
        t = v10 + v6 & 4294967295L
        v14 ^= (t & 33554431) << 7 | t >> 25
        t = v14 + v10 & 4294967295L
        v2 ^= (t & 8388607) << 9 | t >> 23
        t = v2 + v14 & 4294967295L
        v6 ^= (t & 524287) << 13 | t >> 19
        t = v6 + v2 & 4294967295L
        v10 ^= (t & 16383) << 18 | t >> 14
        t = v15 + v11 & 4294967295L
        v3 ^= (t & 33554431) << 7 | t >> 25
        t = v3 + v15 & 4294967295L
        v7 ^= (t & 8388607) << 9 | t >> 23
        t = v7 + v3 & 4294967295L
        v11 ^= (t & 524287) << 13 | t >> 19
        t = v11 + v7 & 4294967295L
        v15 ^= (t & 16383) << 18 | t >> 14
        t = v0 + v3 & 4294967295L
        v1 ^= (t & 33554431) << 7 | t >> 25
        t = v1 + v0 & 4294967295L
        v2 ^= (t & 8388607) << 9 | t >> 23
        t = v2 + v1 & 4294967295L
        v3 ^= (t & 524287) << 13 | t >> 19
        t = v3 + v2 & 4294967295L
        v0 ^= (t & 16383) << 18 | t >> 14
        t = v5 + v4 & 4294967295L
        v6 ^= (t & 33554431) << 7 | t >> 25
        t = v6 + v5 & 4294967295L
        v7 ^= (t & 8388607) << 9 | t >> 23
        t = v7 + v6 & 4294967295L
        v4 ^= (t & 524287) << 13 | t >> 19
        t = v4 + v7 & 4294967295L
        v5 ^= (t & 16383) << 18 | t >> 14
        t = v10 + v9 & 4294967295L
        v11 ^= (t & 33554431) << 7 | t >> 25
        t = v11 + v10 & 4294967295L
        v8 ^= (t & 8388607) << 9 | t >> 23
        t = v8 + v11 & 4294967295L
        v9 ^= (t & 524287) << 13 | t >> 19
        t = v9 + v8 & 4294967295L
        v10 ^= (t & 16383) << 18 | t >> 14
        t = v15 + v14 & 4294967295L
        v12 ^= (t & 33554431) << 7 | t >> 25
        t = v12 + v15 & 4294967295L
        v13 ^= (t & 8388607) << 9 | t >> 23
        t = v13 + v12 & 4294967295L
        v14 ^= (t & 524287) << 13 | t >> 19
        t = v14 + v13 & 4294967295L
        v15 ^= (t & 16383) << 18 | t >> 14
        i += 1

    b0 = b0 + v0 & 4294967295L
    b1 = b1 + v1 & 4294967295L
    b2 = b2 + v2 & 4294967295L
    b3 = b3 + v3 & 4294967295L
    b4 = b4 + v4 & 4294967295L
    b5 = b5 + v5 & 4294967295L
    b6 = b6 + v6 & 4294967295L
    b7 = b7 + v7 & 4294967295L
    b8 = b8 + v8 & 4294967295L
    b9 = b9 + v9 & 4294967295L
    b10 = b10 + v10 & 4294967295L
    b11 = b11 + v11 & 4294967295L
    b12 = b12 + v12 & 4294967295L
    b13 = b13 + v13 & 4294967295L
    b14 = b14 + v14 & 4294967295L
    b15 = b15 + v15 & 4294967295L
    return (
     b0, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12, b13, b14, b15)