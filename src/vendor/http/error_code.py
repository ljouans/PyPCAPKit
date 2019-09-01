# -*- coding: utf-8 -*-
"""HTTP/2 Error Code"""

import csv
import re

from pcapkit.vendor.default import Vendor

__all__ = ['ErrorCode']


def hexlify(code):
    # temp = hex(code)[2:].upper().zfill(8)
    # return f'0x{temp[:4]}_{temp[4:]}'
    return f'0x{hex(code)[2:].upper().zfill(8)}'


class ErrorCode(Vendor):
    """HTTP/2 Error Code"""

    FLAG = 'isinstance(value, int) and 0x00000000 <= value <= 0xFFFFFFFF'
    LINK = 'https://www.iana.org/assignments/http2-parameters/error-code.csv'

    def process(self, data):
        reader = csv.reader(data)
        next(reader)  # header

        enum = list()
        miss = list()
        for item in reader:
            name = item[1]
            dscp = item[2]
            rfcs = item[3]

            temp = list()
            for rfc in filter(None, re.split(r'\[|\]', rfcs)):
                if 'RFC' in rfc:
                    temp.append(f'[{rfc[:3]} {rfc[3:]}]')
                else:
                    temp.append(f'[{rfc}]')
            desc = f" {''.join(temp)}" if rfcs else ''
            dscp = f' {dscp}' if dscp else ''

            try:
                temp = int(item[0], base=16)
                code = hexlify(temp)
                renm = self.rename(name, code)

                pres = f"{self.NAME}[{renm!r}] = {code}"
                sufs = f'#{desc}{dscp}' if desc or dscp else ''

                if len(pres) > 74:
                    sufs = f"\n{' '*80}{sufs}"

                enum.append(f'{pres.ljust(76)}{sufs}')
            except ValueError:
                start, stop = map(lambda s: int(s, base=16), item[0].split('-'))

                miss.append(f'if {hexlify(start)} <= value <= {hexlify(stop)}:')
                if desc or dscp:
                    miss.append(f'#{desc}{dscp}')
                miss.append('    temp = hex(value)[2:].upper().zfill(8)')
                miss.append(f"    extend_enum(cls, '{name} [0x%s]' % (temp[:4]+'_'+temp[4:]), value)")
                miss.append('    return cls(value)')
        return enum, miss


if __name__ == "__main__":
    ErrorCode()
