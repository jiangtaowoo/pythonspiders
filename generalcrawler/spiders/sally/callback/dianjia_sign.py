# -*- coding: UTF-8 -*-
import urllib

class PyBitOperator(object):
    def __init__(self, num=0):
        self.num = num
        
    def bit_wise(self, binstr):
        return ''.join(map(lambda x: '1' if x=='0' else '0', binstr))
        
    def num_to_binstr(self, num):
        if isinstance(num, int) or isinstance(num, long):
            if num<0:
                binstr = '0'*32
                binnum = bin(-num-1)[2:]
                binstr = binstr[:32-len(binnum)] + binnum
                binstr = self.bit_wise(binstr)
                return binstr
            else:
                binstr = '0'*32
                binnum = bin(num)[2:]
                binstr = binstr[:32-len(binnum)] + binnum
                return binstr
        return None

    def binstr_to_num(self, binstr, force_positive=False):
        if binstr[0]=='1' and not force_positive:
            #negative number
            #bit reverse and +1
            binstr = self.bit_wise(binstr)
            return -(int(binstr,2)+1)
        else:
            return int(binstr,2)
           
    def Lshift(self, num, shift_bits):
        shift_bits %= 32
        binstr = self.num_to_binstr(num)
        binstr = binstr[shift_bits:] + '0'*shift_bits
        return self.binstr_to_num(binstr)
        
    def ZRshift(self, num, shift_bits):
        shift_bits %= 32
        force_positive = True if shift_bits==0 else False
        binstr = self.num_to_binstr(num)
        binstr = '0'*shift_bits + binstr[:32-shift_bits]
        return self.binstr_to_num(binstr, force_positive)
        
        
class DianjiaPassSign(object):
    def __init__(self):
        pass
    
    def encode_password(self, pass_str):
        bitOp = PyBitOperator()
        return self.wrap_func(bitOp, pass_str)

    def wrap_func(self, bitOp, pass_str):
        def auto_scale_list(listx, need_idx):
            if isinstance(listx, list):
                while need_idx>=len(listx):
                    listx.append(0)
                return listx
            else:
                listnew = [listx]
                while need_idx>=len(listnew):
                    listnew.append(0)
                return listnew
            
        def i(e,t):
            a = (65535 & e) + (65535 & t)
            n = (e >> 16) + (t >> 16) + (a >> 16)
            return bitOp.Lshift(n,16) | 65535 & a

        def s(e,t):
            return bitOp.Lshift(e,t) | bitOp.ZRshift(e,32- t)
        
        def o(e, t, a, n, r, o):
            return i(s(i(i(t, e), i(n, o)), r), a)
            
        def d(e, t, a, n, r, i, s):
            return o(t & a | ~t & n, e, t, r, i, s)
        
        def u(e, t, a, n, r, i, s):
            return o(t & n | a & ~n, e, t, r, i, s)
        
        def l(e, t, a, n, r, i, s):
            return o(t ^ a ^ n, e, t, r, i, s)
        
        def _(e, t, a, n, r, i, s):
            return o(a ^ (t | ~n), e, t, r, i, s)
        
        def m(e, t):
            e_idx = t >> 5
            e = auto_scale_list(e, e_idx)
            e[e_idx] |= bitOp.Lshift(128, t % 32)
            e_idx = bitOp.ZRshift(t+64, bitOp.Lshift(9,4))+14 #(t + 64 >>> 9 << 4) + 14
            e = auto_scale_list(e, e_idx)
            e[e_idx] = t
            a, n, r, s, o = (None,None,None,None,None)
            m = 1732584193
            c = - 271733879
            h = - 1732584194
            M = 271733878
            for a in xrange(0, len(e), 16):
                n = m
                r = c
                s = h
                o = M
                e = auto_scale_list(e, a)
                m = d(m, c, h, M, e[a], 7, - 680876936)
                e = auto_scale_list(e, a+1)
                M = d(M, m, c, h, e[a + 1], 12, - 389564586)
                e = auto_scale_list(e, a+2)
                h = d(h, M, m, c, e[a + 2], 17, 606105819)
                e = auto_scale_list(e, a+3)
                c = d(c, h, M, m, e[a + 3], 22, - 1044525330)
                e = auto_scale_list(e, a+4)
                m = d(m, c, h, M, e[a + 4], 7, - 176418897)
                e = auto_scale_list(e, a+5)
                M = d(M, m, c, h, e[a + 5], 12, 1200080426)
                e = auto_scale_list(e, a+6)
                h = d(h, M, m, c, e[a + 6], 17, - 1473231341)
                e = auto_scale_list(e, a+7)
                c = d(c, h, M, m, e[a + 7], 22, - 45705983)
                e = auto_scale_list(e, a+8)
                m = d(m, c, h, M, e[a + 8], 7, 1770035416)
                e = auto_scale_list(e, a+9)
                M = d(M, m, c, h, e[a + 9], 12, - 1958414417)
                e = auto_scale_list(e, a+10)
                h = d(h, M, m, c, e[a + 10], 17, - 42063)
                e = auto_scale_list(e, a+11)
                c = d(c, h, M, m, e[a + 11], 22, - 1990404162)
                e = auto_scale_list(e, a+12)
                m = d(m, c, h, M, e[a + 12], 7, 1804603682)
                e = auto_scale_list(e, a+13)
                M = d(M, m, c, h, e[a + 13], 12, - 40341101)
                e = auto_scale_list(e, a+14)
                h = d(h, M, m, c, e[a + 14], 17, - 1502002290)
                xxx_e = e[a+15] if a+15<len(e) else 0
                c = d(c, h, M, m, xxx_e, 22, 1236535329)
                e = auto_scale_list(e, a+1)
                m = u(m, c, h, M, e[a + 1], 5, - 165796510)
                e = auto_scale_list(e, a+6)
                M = u(M, m, c, h, e[a + 6], 9, - 1069501632)
                e = auto_scale_list(e, a+11)
                h = u(h, M, m, c, e[a + 11], 14, 643717713)
                e = auto_scale_list(e, a)
                c = u(c, h, M, m, e[a], 20, - 373897302)
                e = auto_scale_list(e, a+5)
                m = u(m, c, h, M, e[a + 5], 5, - 701558691)
                e = auto_scale_list(e, a+10)
                M = u(M, m, c, h, e[a + 10], 9, 38016083)
                xxx_e = e[a+15] if a+15<len(e) else 0
                h = u(h, M, m, c, xxx_e, 14, - 660478335)
                e = auto_scale_list(e, a+4)
                c = u(c, h, M, m, e[a + 4], 20, - 405537848)
                e = auto_scale_list(e, a+9)
                m = u(m, c, h, M, e[a + 9], 5, 568446438)
                e = auto_scale_list(e, a+14)
                M = u(M, m, c, h, e[a + 14], 9, - 1019803690)
                e = auto_scale_list(e, a+3)
                h = u(h, M, m, c, e[a + 3], 14, - 187363961)
                e = auto_scale_list(e, a+8)
                c = u(c, h, M, m, e[a + 8], 20, 1163531501)
                e = auto_scale_list(e, a+13)
                m = u(m, c, h, M, e[a + 13], 5, - 1444681467)
                e = auto_scale_list(e, a+2)
                M = u(M, m, c, h, e[a + 2], 9, - 51403784)
                e = auto_scale_list(e, a+7)
                h = u(h, M, m, c, e[a + 7], 14, 1735328473)
                e = auto_scale_list(e, a+12)
                c = u(c, h, M, m, e[a + 12], 20, - 1926607734)
                e = auto_scale_list(e, a+5)
                m = l(m, c, h, M, e[a + 5], 4, - 378558)
                e = auto_scale_list(e, a+8)
                M = l(M, m, c, h, e[a + 8], 11, - 2022574463)
                e = auto_scale_list(e, a+11)
                h = l(h, M, m, c, e[a + 11], 16, 1839030562)
                e = auto_scale_list(e, a+14)
                c = l(c, h, M, m, e[a + 14], 23, - 35309556)
                e = auto_scale_list(e, a+1)
                m = l(m, c, h, M, e[a + 1], 4, - 1530992060)
                e = auto_scale_list(e, a+4)
                M = l(M, m, c, h, e[a + 4], 11, 1272893353)
                e = auto_scale_list(e, a+7)
                h = l(h, M, m, c, e[a + 7], 16, - 155497632)
                e = auto_scale_list(e, a+10)
                c = l(c, h, M, m, e[a + 10], 23, - 1094730640)
                e = auto_scale_list(e, a+13)
                m = l(m, c, h, M, e[a + 13], 4, 681279174)
                e = auto_scale_list(e, a)
                M = l(M, m, c, h, e[a], 11, - 358537222)
                e = auto_scale_list(e, a+3)
                h = l(h, M, m, c, e[a + 3], 16, - 722521979)
                e = auto_scale_list(e, a+6)
                c = l(c, h, M, m, e[a + 6], 23, 76029189)
                e = auto_scale_list(e, a+9)
                m = l(m, c, h, M, e[a + 9], 4, - 640364487)
                e = auto_scale_list(e, a+12)
                M = l(M, m, c, h, e[a + 12], 11, - 421815835)
                xxx_e = e[a+15] if a+15<len(e) else 0
                h = l(h, M, m, c, xxx_e, 16, 530742520)
                e = auto_scale_list(e, a+2)
                c = l(c, h, M, m, e[a + 2], 23, - 995338651)
                e = auto_scale_list(e, a)
                m = _(m, c, h, M, e[a], 6, - 198630844)
                e = auto_scale_list(e, a+7)
                M = _(M, m, c, h, e[a + 7], 10, 1126891415)
                e = auto_scale_list(e, a+14)
                h = _(h, M, m, c, e[a + 14], 15, - 1416354905)
                e = auto_scale_list(e, a+5)
                c = _(c, h, M, m, e[a + 5], 21, - 57434055)
                e = auto_scale_list(e, a+12)
                m = _(m, c, h, M, e[a + 12], 6, 1700485571)
                e = auto_scale_list(e, a+3)
                M = _(M, m, c, h, e[a + 3], 10, - 1894986606)
                e = auto_scale_list(e, a+10)
                h = _(h, M, m, c, e[a + 10], 15, - 1051523)
                e = auto_scale_list(e, a+1)
                c = _(c, h, M, m, e[a + 1], 21, - 2054922799)
                e = auto_scale_list(e, a+8)
                m = _(m, c, h, M, e[a + 8], 6, 1873313359)
                xxx_e = e[a+15] if a+15<len(e) else 0
                M = _(M, m, c, h, xxx_e, 10, - 30611744)
                e = auto_scale_list(e, a+6)
                h = _(h, M, m, c, e[a + 6], 15, - 1560198380)
                e = auto_scale_list(e, a+13)
                c = _(c, h, M, m, e[a + 13], 21, 1309151649)
                e = auto_scale_list(e, a+4)
                m = _(m, c, h, M, e[a + 4], 6, - 145523070)
                e = auto_scale_list(e, a+11)
                M = _(M, m, c, h, e[a + 11], 10, - 1120210379)
                e = auto_scale_list(e, a+2)
                h = _(h, M, m, c, e[a + 2], 15, 718787259)
                e = auto_scale_list(e, a+9)
                c = _(c, h, M, m, e[a + 9], 21, - 343485551)
                m = i(m, n)
                c = i(c, r)
                h = i(h, s)
                M = i(M, o)
            return [m,c,h,M]
        
        def c(e):
            t = None
            a = ''
            for t in xrange(0, 32*len(e), 8):
                a += chr(bitOp.ZRshift(e[t >> 5], (t % 32)) & 255)
            return a
        
        def h(e):
            t = None
            a = []
            idx = (len(e) >> 2) - 1
            a = auto_scale_list(a, idx)
            for t in xrange(0, 8*len(e), 8):
                a_idx = t >> 5
                auto_scale_list(a, a_idx)
                a[a_idx] |= bitOp.Lshift((255 & ord(e[t / 8])), t % 32)
            return a

        def M(e):
            return c(m(h(e), 8 * len(e)))

        def f(e, t):
            a, n = None, None
            r = h(e)
            i = [0]*15
            s = [0]*15
            if len(r)>16:
                r = m(r, 8 * len(e))
            for a in xrange(0,16):
                i[a] = 909522486 ^ r[a],
                s[a] = 1549556828 ^ r[a]
            n = m(i.extend(h(t)), 512 + 8 * len(t))
            return c(m(s.extend(n), 640))

        def p(e):
            t, a = None, None
            n = '0123456789abcdef'
            r = ''
            for a in xrange(0,len(e)):
                t = ord(e[a])
                r = r + n[bitOp.ZRshift(t,4) & 15] + n[15 & t]
            return r

        def y(e):
            return urllib.unquote(urllib.quote(e.encode('utf-8'))).decode('utf-8')

        def g(e):
            return M(y(e))

        def L(e):
            return p(g(e))

        def Y(e, t):
            return f(y(e), y(t))

        def k(e, t):
            return p(Y(e, t))

        def D(e, t, a):
            if t:
                if a:
                    return Y(t, e)
                else:
                    return k(t, e)
            else:
                if a:
                    return g(e)
                else:
                    return L(e)
                    
        return D(pass_str, None, None)