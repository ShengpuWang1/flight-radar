import numpy as np
from scipy import complex64, signal
import pyModeS as pms
# from tqdm import tqdm


def adsb_select(msg):
    flight = {
        'df': pms.adsb.df(msg),
        'tpc': pms.adsb.typecode(msg)
        }
    if (flight['df'] != 17 and flight['df'] != 18) or flight['tpc'] < 1 or flight['tpc'] > 22:
        raise Exception('not useful')


def list2bytes(bl):  # Boolean list
    msg = ''
    for i in range(0, len(bl), 8):
        ls = bl[i:i+8]
        msg += int(np.packbits(ls)[0]).to_bytes(1, 'big').hex()
    return msg


# n = 16M, fs = 3.2 MHz, T = 5.0 s
thd = 5.0
msgs = []  # list of 28-letter(112-bit) hex string

cpt_cplx = np.fromfile(open('capture.cfile'), dtype=complex64)
print('captured data: ', type(cpt_cplx), len(cpt_cplx))

# get amplitude
cpt_abs = np.abs(cpt_cplx)
# resample to 4 MHz
cpt_abs = signal.resample(cpt_abs, int(len(cpt_abs) * 5/4))
N = len(cpt_abs)
fs = 4  # MHz

# big components
idx_1 = [i for i, s in enumerate(cpt_abs) if s > 5]
print('signals under test: ', len(idx_1))
idx_old = - 481
for idx in idx_1:
    if idx < idx_old + 480:
        continue
    sut = cpt_abs[idx:idx+500]
    sut = (sut > sut[0]/2).astype(int)
    sut = sut[::2]
    if np.packbits(sut[0:10])[0] == 161:
        sut = sut[16:]
        sut_bl = [(sut[i] > sut[i+1]) for i in range(0, len(sut), 2)][0:112]  # 112 bits = 14 bytes
        msg = list2bytes(sut_bl)  # 14 * 2 = 28 hexdigits string
        try:
            _ = adsb_select(msg)
            msgs.append(msg)
            idx_old = idx
        except:
            pass

print('useful signal: ', len(msgs))

file = open('msgs.txt', 'w')
file.writelines(msgs)
file.close()
