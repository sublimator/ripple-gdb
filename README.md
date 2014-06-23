## ripple-gdb

### Requirements

* Ubuntu >= 14.04 LTS
* GDB built with Python >= 3.4 (default on ubuntu >= 14.04)

### Install
#### Option 1

```
sudo apt-get install python3-setuptools
sudo apt-get install python3-pip
sudo pip3 install git+https://github.com/sublimator/ripple-gdb.git
```

#### Option 2 (develop mode)

```
sudo apt-get install python3-setuptools
git clone https://github.com/sublimator/ripple-gdb.git
cd ripple-gdb; sudo python3 setup.py develop
```

### Basic Usage

```
(gdb) python import ripplegdb
(gdb) p accountID
$1 = rETUzjaVm3iJuDfUbTEqxPaUqPyuurwy5c
(gdb) trp
ripple-printers disabled
(gdb) trp
ripple-printers enabled
(gdb) rlr
Reloading ripplegdb...done.
```

### Debugging a core file
```
✗ gdb build/rippled core.14610 -ex "python import ripplegdb" -ex "set height 0"
...
(gdb) thread 4
[Switching to thread 4 (Thread 0x7fffa6ffd700 (LWP 14635))]
#0  ripple::path::rippleCalculate (activeLedger=..., saMaxAmountAct=0E-100/USD/rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B,
    saDstAmountAct=0E-100/JPY/rMAz5ZnK73nyNUL4foAvaxdreczCkG3vA6, pathStateList=std::vector of length 3, capacity 4 = {...},
    saMaxAmountReq=47.13359976517965/USD/rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B:(sfSendMax),
    saDstAmountReq=5000.000000000000/JPY/rMAz5ZnK73nyNUL4foAvaxdreczCkG3vA6:(sfAmount), uDstAccountID=..., uSrcAccountID=...,
    spsPaths=TODO: STPathSet, bPartialPayment=true, bLimitQuality=false, bNoRippleDirect=false, bStandAlone=false,
    bOpenLedger=true) at src/ripple/module/app/paths/RippleCalc.cpp:215
215     int iPass   = 0;
(gdb) p saMaxAmountAct
$1 = 0E-100/USD/rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B
```
### Why?

```
(gdb) trp
ripple-printers disabled
(gdb) p saMaxAmountReq
$7 = (const ripple::STAmount &) @0x7fffa6ff6b10: {<ripple::SerializedType> = {_vptr.SerializedType = 0x2cb4a50 <vtable for ripple::STAmount+16>,
    fName = 0x33e6220 <ripple::sfSendMax>}, static cMinOffset = -96, static cMaxOffset = 80, static cMinValue = 1000000000000000,
  static cMaxValue = 9999999999999999, static cMaxNative = 9000000000000000000, static cMaxNativeN = 100000000000000000, static cNotNative = 9223372036854775808,
  static cPosNative = 4611686018427387904, static uRateOne = 6125895493223874560, mCurrency = {pn = {0, 0, 0, 4477781, 0}, static bytes = <optimized out>},
  mIssuer = {pn = {3367182346, 841304159, 3146602409, 1555583033, 3516163488}, static bytes = <optimized out>}, mValue = 4713359976517965, mOffset = -14,
  mIsNative = false, mIsNegative = false}
```

Because (sometimes) you'd prefer to see:

```
(gdb) trp
ripple-printers enabled
(gdb) p saMaxAmountReq
$8 = 47.13359976517965/USD/rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B:(sfSendMax)
```

### Notes

* This inlines std library pretty printers converted to work with Python

### TODO

* Usage documentation
* Contributor documentation
