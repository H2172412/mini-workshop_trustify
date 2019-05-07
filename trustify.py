
#------------------------------------------------------------------------------
# LICENSE: The MIT License (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# https://github.com/SiliconCraft/sic43nt-server-pythonflask/blob/master/LICENSE.txt
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @copyright 2018 Silicon Craft Technology Co.,Ltd.
# @license   https://github.com/SiliconCraft/sic43nt-server-pythonflask/blob/master/LICENSE.txt
# @link      https://github.com/SiliconCraft/sic43nt-server-pythonflask
#
# This source code is based on The stream cipher MICKEY (version 1) by Steve Babbage 
# and Matthew Dodd, published on April 29, 2005. The source file is mainly a direct porting 
# from mickey_v1.c in folder "C code MICKEY v1 faster" of 
# http://www.ecrypt.eu.org/stream/ciphers/mickey/mickeysource.zip which is implemented 
# in C language to PHP. However, there are additional function to handle string of bit 
# and arithmetic shift operation.
# 
# Credit #1: The first JavaScript porting is done by Tanawat Hongthai in 2017
# 
# For original information regarding to Mickey v1 algorithm, please refer to 
# http://www.ecrypt.eu.org/stream/ciphers/mickey/
#
#------------------------------------------------------------------------------

M32 = 0xffffffff
class Encrypt:
    r = [None] * 3
    s = [None] * 3

    
class Keystream:
    R_MASK = [0x1d5363d5, 0x415a0aac, 0x0000d2a8]
    COMP0 = [0x6aa97a30, 0x7942a809, 0x00003fea]
    COMP1 = [0xdd629e9a, 0xe3a21d63, 0x00003dd7]
    S_MASK0 = [0x9ffa7faf, 0xaf4a9381, 0x00005802]
    S_MASK1 = [0x4c8cb877, 0x4911b063, 0x0000c52b]

    def clock_r(self, encrypt, input_bit, control_bit):
        r0 = encrypt.r[0]
        r1 = encrypt.r[1]
        r2 = encrypt.r[2]
        feedback_bit = ((r2 >> 15) & 1) ^ input_bit
        carry0 = (r0 >> 31) & 1
        carry1 = (r1 >> 31) & 1

        if control_bit != 0:
            r0 ^= (r0 << 1) & M32
            r1 ^= ((r1 << 1) ^ carry0) & M32
            r2 ^= ((r2 << 1) ^ carry1) & M32
        else:
            r0 = (r0 << 1) & M32
            r1 = ((r1 << 1) ^ carry0) & M32
            r2 = ((r2 << 1) ^ carry1) & M32

        if feedback_bit != 0:
            r0 ^= self.R_MASK[0]
            r1 ^= self.R_MASK[1]
            r2 ^= self.R_MASK[2]

        encrypt.r[0] = r0
        encrypt.r[1] = r1
        encrypt.r[2] = r2

    def clock_s(self, encrypt, input_bit, control_bit):
        s0 = encrypt.s[0]
        s1 = encrypt.s[1]
        s2 = encrypt.s[2]
        feedback_bit = ((s2 >> 15) & 1) ^ input_bit
        carry0 = (s0 >> 31) & 1
        carry1 = (s1 >> 31) & 1
        s0 = M32 & (s0 << 1) ^ ((s0 ^ self.COMP0[0]) & ((s0 >> 1) ^ (s1 << 31) ^ self.COMP1[0]) & 0xfffffffe)
        s1 = M32 & (s1 << 1) ^ ((s1 ^ self.COMP0[1]) & ((s1 >> 1) ^ (s2 << 31) ^ self.COMP1[1])) ^ carry0
        s2 = M32 & (s2 << 1) ^ ((s2 ^ self.COMP0[2]) & ((s2 >> 1) ^ self.COMP1[2]) & 0x7fff) ^ carry1

        if feedback_bit != 0:
            if control_bit != 0:
                s0 ^= self.S_MASK1[0]
                s1 ^= self.S_MASK1[1]
                s2 ^= self.S_MASK1[2]
            else:
                s0 ^= self.S_MASK0[0]
                s1 ^= self.S_MASK0[1]
                s2 ^= self.S_MASK0[2]

        encrypt.s[0] = s0
        encrypt.s[1] = s1
        encrypt.s[2] = s2
        
    def clock_kg(self, encrypt, mixing, input_bit):
        r0 = encrypt.r[0]
        r1 = encrypt.r[1]
        s0 = encrypt.s[0]
        s1 = encrypt.s[1]
        key_stream_bit = (r0 ^ s0) & 1
        control_bit_r = ((s0 >> 27) ^ (r1 >> 21)) & 1
        control_bit_s = ((s1 >> 21) ^ (r0 >> 26)) & 1

        if mixing != 0:
            self.clock_r(encrypt, ((s1 >> 8) & 1) ^ input_bit, control_bit_r)
        else:
            self.clock_r(encrypt, input_bit, control_bit_r)

        self.clock_s(encrypt, input_bit, control_bit_s)

        return key_stream_bit

    def setup(self, encrypt, key, iv):
        key_size = len(key)
        iv_size = len(iv)

        for i in range(3):
            encrypt.r[i] = 0
            encrypt.s[i] = 0

        for i in range(iv_size):
            iv_key_bit = (int(iv[i]) - ord('0')) & 1
            self.clock_kg(encrypt, 1, iv_key_bit)

        for i in range(key_size):
            iv_key_bit = (int(key[i]) - ord('0')) & 1
            self.clock_kg(encrypt, 1, iv_key_bit)

        for i in range(80):
            self.clock_kg(encrypt, 1, 0)

    def stream(self, key, iv, length):
        resource = ""
        encrypt = Encrypt()
        key_bin = bin(int("80" + key, 16))[10:]
        iv_bin = bin(int("80" + iv, 16))[10:]
        key_reverse = key_bin[::-1]
        iv_reverse = iv_bin[::-1]
        self.setup(encrypt, key_reverse, iv_reverse)

        for i in range(length):
            t_keystream = 0

            for j in range(8):
                t_keystream ^= M32 & (self.clock_kg(encrypt, 0, 0) << int(7-j))

            key_result = str(hex(t_keystream)).replace('0x', '')
            resource = resource + "00"[0:2-len(key_result)] + key_result

        return resource