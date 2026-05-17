b = b'\n4spot@public.aggre.bookTicker.v3.api.pb@100ms@BTCUSDT\x1a\x07BTCUSDT0\x8a\xa2\xc7\xa2\xe33\xda\x13-\n\x0878161.17\x12\x0b17.55793416\x1a\x0878161.18"\n0.10677647'
s = b.decode('ascii', errors='ignore')
print(repr(s))
