from myhdl import intbv

from common.packed_struct import StructDescription, BitVector

CcipClAddr = BitVector(42)
CcipClData = BitVector(512)
CcipMData = BitVector(16)
CcipClNum = BitVector(2)

CcipC0Rsp = BitVector(4)
eRSP_RDLINE = intbv(0x0)[4:0]
eRSP_UMSG = intbv(0x4)[4:0]

CcipC1Rsp = BitVector(4)
eRSP_WRDLINE = intbv(0x0)[4:0]
eRSP_WRFENCE = intbv(0x4)[4:0]
eRSP_INTR = intbv(0x6)[4:0]

CcipVc = BitVector(2)

CcipMmioAddr = BitVector(16)
CcipMmioData = BitVector(64)
CcipTid = BitVector(9)

CcipClLen = BitVector(2)
eCL_LEN_1 = intbv(0b00)[2:0]
eCL_LEN_2 = intbv(0b01)[2:0]
eCL_LEN_4 = intbv(0b11)[2:0]

CcipC0Req = BitVector(4)
eREQ_RDLINE_I = intbv(0x0)[4:0]
eREQ_RDLINE_S = intbv(0x1)[4:0]

CcipC1Req = BitVector(4)
eREQ_WRLINE_I = intbv(0x0)[4:0]
eREQ_WRLINE_M = intbv(0x1)[4:0]
eREQ_WRPUSH_I = intbv(0x2)[4:0]
eREQ_WRFENCE = intbv(0x4)[4:0]
eREQ_INTR = intbv(0x6)[4:0]


class CcipC0ReqMmioHdr(StructDescription):
    address = CcipMmioAddr
    length = BitVector(2)
    rsvd = BitVector(1)
    tid = CcipTid


class CcipC0RspMemHdr(StructDescription):
    vc_used = CcipVc
    rsvd1 = BitVector(1)
    hit_miss = BitVector(1)
    rsvd0 = BitVector(2)
    cl_num = CcipClNum
    resp_type = CcipC0Rsp
    mdata = CcipMData


class CcipC1RspMemHdr(StructDescription):
    vc_used = CcipVc
    rsvd1 = BitVector(1)
    hit_miss = BitVector(1)
    format = BitVector(1)
    rsvd0 = BitVector(1)
    cl_num = CcipClNum
    resp_type = CcipC1Rsp
    mdata = CcipMData


class CcipC0Rx(StructDescription):
    hdr = CcipC0RspMemHdr
    data = CcipClData
    rspValid = BitVector(1)
    mmioRdValid = BitVector(1)
    mmioWrValid = BitVector(1)


class CcipC1Rx(StructDescription):
    hdr = CcipC1RspMemHdr
    rspValid = BitVector(1)


class CcipRx(StructDescription):
    c0TxAlmFull = BitVector(1)
    c1TxAlmFull = BitVector(1)
    c0 = CcipC0Rx
    c1 = CcipC1Rx


class CcipC0ReqMemHdr(StructDescription):
    vc_sel = CcipVc
    rsvd1 = BitVector(2)
    cl_len = CcipClLen
    req_type = CcipC0Req
    rsvd0 = BitVector(6)
    address = CcipClAddr
    mdata = CcipMData


class CcipC1ReqMemHdr(StructDescription):
    rsvd2 = BitVector(6)
    vc_sel = CcipVc
    sop = BitVector(1)
    rsvd1 = BitVector(1)
    cl_len = CcipClLen
    req_type = CcipC1Req
    rsvd0 = BitVector(6)
    address = CcipClAddr
    mdata = CcipMData


class CcipC2RspMmioHdr(StructDescription):
    tid = CcipTid


class CcipC0Tx(StructDescription):
    hdr = CcipC0ReqMemHdr
    valid = BitVector(1)


class CcipC1Tx(StructDescription):
    hdr = CcipC1ReqMemHdr
    data = CcipClData
    valid = BitVector(1)


class CcipC2Tx(StructDescription):
    hdr = CcipC2RspMmioHdr
    mmioRdValid = BitVector(1)
    data = CcipMmioData


class CcipTx(StructDescription):
    c0 = CcipC0Tx
    c1 = CcipC1Tx
    c2 = CcipC2Tx
