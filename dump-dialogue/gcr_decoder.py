from common_helpers import *


class GCRDecoder:
    @staticmethod
    def decode_gcr_bytes(gcr_bytes):
        if len(gcr_bytes) % 5 != 0:
            raise Exception("GCR bytes not multiple of 5")

        gcr_offset = 0
        decoded_bytes = []
        while gcr_offset < len(gcr_bytes):
            gcr_group = gcr_bytes[gcr_offset:gcr_offset+5]
            decoded_group = GCRDecoder.decode_gcr_bits(gcr_group)
            decoded_bytes.extend(decoded_group)
            gcr_offset += 5
        return decoded_bytes

    @staticmethod
    def decode_gcr_bits(_bytes):
        decoder = {
            10 : 0, #"01010" : "0000",
            11 : 1, #"01011" : "0001",
            18 : 2, #"10010" : "0010",
            19 : 3, #"10011" : "0011",
            14 : 4, #"01110" : "0100",
            15 : 5, #"01111" : "0101",
            22 : 6, #"10110" : "0110",
            23 : 7, #"10111" : "0111",
            9 : 8,  #"01001" : "1000",
            25 : 9, #"11001" : "1001",
            26 : 10, #"11010" : "1010",
            27 : 11, #"11011" : "1011",
            13 : 12, #"01101" : "1100",
            29 : 13, #"11101" : "1101",
            30 : 14, #"11110" : "1110",
            21 : 15, #"10101" : "1111"
            }

        #Decode 40 bits into 32 (5:4 bytes)
        #0       A7,A6,A5,A4,A3
        #1       A2,A1,A0,B7,B6
        #2       B5,B4,B3,B2,B1
        #3       B0,C7,C6,C5,C4

        #4       C3,C2,C1,C0,D7
        #5       D6,D5,D4,D3,D2
        #6       D1,D0,E7,E6,E5
        #7       E4,E3,E2,E1,E0
        bits = []
        a1 = _bytes[0] & 0b11111000
        a2 = _bytes[0] & 0b00000111
        b1 = _bytes[1] & 0b11000000
        b2 = _bytes[1] & 0b00111110
        b3 = _bytes[1] & 0b00000001
        c1 = _bytes[2] & 0b11110000
        c2 = _bytes[2] & 0b00001111
        d1 = _bytes[3] & 0b10000000
        d2 = _bytes[3] & 0b01111100
        d3 = _bytes[3] & 0b00000011
        e1 = _bytes[4] & 0b11100000
        e2 = _bytes[4] & 0b00011111
        A1 = a1 >> 3
        A2 = a2 << 2
        B1 = b1 >> 6
        B2 = b2 >> 1
        B3 = b3 << 4
        C1 = c1 >> 4
        C2 = c2 << 1
        D1 = d1 >> 7
        D2 = d2 >> 2
        D3 = d3 << 3
        E1 = e1 >> 5
        E2 = e2

        bits.append(A1)
        bits.append(A2 | B1)
        bits.append(B2)
        bits.append(B3 | C1)
        bits.append(C2 | D1)
        bits.append(D2)
        bits.append(D3 | E1)
        bits.append(E2)

        decoded_nibbles = []
        for i in range(0, 8):
            try:
                decoded_nibble = decoder[bits[i]]
            except:
                print(str("GCR error - Byte value found: " + hex(bits[i]) + " at position " + str(i)))
                print(repr_hex_bytes(_bytes))
                print(repr_hex_bytes(bits))
                decoded_nibble = 0xFF
            decoded_nibbles.append(decoded_nibble)

        decoded_bytes = []
        for i in range(0, 4):
            decoded_bytes.append(decoded_nibbles[i * 2] << 4 | decoded_nibbles[i * 2 + 1])
        return decoded_bytes
