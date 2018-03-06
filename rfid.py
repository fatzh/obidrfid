# -*- coding: utf-8 -*-
import ctypes

libfetcp = ctypes.CDLL('libfetcp.so')
libfeisc = ctypes.CDLL('libfeisc.so')

# default port
PORT = 10001


def rfid_connect(ip, port):
    '''
    Connect to the RFID antenna
    '''
    port_handle = libfetcp.FETCP_Connect(ip.encode(), port)
    if (port_handle > 0):
        print('Port connected...')
        reader_handle = libfeisc.FEISC_NewReader(port_handle)
        if (reader_handle > 0):
            back = libfeisc.FEISC_SetReaderPara(
                reader_handle,
                ctypes.c_char_p(b'FrameSupport'),
                ctypes.c_char_p(b'Advanced')
            )
            print('Reader initialized, set param {}'.format(back))
            return reader_handle
        else:
            print('--- ! Reader can not be initializer, error {}'.format(reader_handle))
    else:
        print('--- ! Connection failed, error {}'.format(port_handle))

    return None


def rfid_read(reader):
    '''
    Read tags
    '''
    sReqData = (ctypes.c_ubyte * 64)()
    sReqData[0] = 0x01
    sReqData[1] = 0x00

    iReqLen = ctypes.c_int(2)

    sRespData = (ctypes.c_ubyte * 1024)()
    iRespLen = ctypes.c_int()

    reader_read = libfeisc.FEISC_0xB0_ISOCmd
    reader_read.argtypes = [
        ctypes.c_int,
        ctypes.c_ubyte,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
    ]

    back = libfeisc.FEISC_0xB0_ISOCmd(
        reader,                 # reader ID
        ctypes.c_ubyte(255),    # bus addr, I don't think that's relevant for TCP/IP..
        sReqData,                   # request data, unsigned char *
        iReqLen,
        sRespData,
        ctypes.byref(iRespLen),
        2
    )

    # return values
    transponders = []
    if back == 0:
        if iRespLen.value > 0:
            result = sRespData[2:iRespLen.value]
            # split in sizes of 20 elements
            size = 20
            transponders_bytes = [result[i:i + size] for i in range(len(result))[::size]]
            for t in transponders_bytes:
                # first 2 is TR-TYPE
                tr_type = bytearray(t[:2]).decode('utf8')
                dsfid = bytearray(t[2:4]).decode('utf8')
                iid = bytearray(t[4:]).decode('utf8')
                transponders.append({
                    'tr_type': tr_type,
                    'dsfid': dsfid,
                    'iid': iid,
                })

        elif back > 1:
            print('Status: {}'.format(rfid_status_text(back)))
        elif back < 0:
            print('Error: {}'.format(rfid_error_text(back)))

    return transponders


def rfid_reader_info(reader):
    '''
    Print reader info
    '''
    ucInfo = (ctypes.c_ubyte * 300)()
    reader_info = libfeisc.FEISC_0x66_ReaderInfo
    reader_info.argtypes = [
        ctypes.c_int,
        ctypes.c_ubyte,
        ctypes.c_ubyte,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_int
    ]

    back = reader_info(reader, ctypes.c_ubyte(255), 0x00, ucInfo, 0)
    if (back == 0):
        print('Reader: {}'.format(ucInfo[4]))
    elif (back > 0):
        print('--- ! Reader info status {}'.format(rfid_status_text(back)))
    else:
        print('--- ! Reader info error {}'.format(back))
        print(rfid_error_text(ctypes.c_int(back)))


def rfid_reader_lan_configuration_read(reader):
    '''
    Print reader lan configuration,
    If successfull, returns the 14 byts configuration
    to use with the write function below
    '''
    ucConfBlock = (ctypes.c_ubyte * 14)()
    reader_conf = libfeisc.FEISC_0x80_ReadConfBlock
    reader_conf.argtypes = [
        ctypes.c_int,
        ctypes.c_ubyte,
        ctypes.c_ubyte,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_int
    ]

    # read from configuration block 168. This is actually the block 40
    # prepended with the bytes 1 and 0 to read from the EEPROM
    back = reader_conf(reader, ctypes.c_ubyte(255), 168, ucConfBlock, 0)
    if (back == 0):
        return ucConfBlock
    elif (back > 0):
        print('--- ! Reader conf status {}'.format(rfid_status_text(back)))
    else:
        print('--- ! Reader conf error {}'.format(back))
        print(rfid_error_text(ctypes.c_int(back)))


def rfid_reader_lan_configuration_write(reader, conf, ip):
    '''
    Write LAN reader configuration,
    input is the reader handler, the 14 bytes configuration block
    as obtained from the 'read' function above
    and an array with the new ip, e.g. [192, 168, 142, 12]
    This will be written to the EPPROM and requires a SystemReset
    to be saved in the configuration.
    '''
    if len(ip) != 4:
        print('Invalid ip, expected array of 4 numbers.')
        return False

    reader_conf = libfeisc.FEISC_0x81_WriteConfBlock
    reader_conf.argtypes = [
        ctypes.c_int,
        ctypes.c_ubyte,
        ctypes.c_ubyte,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_int
    ]

    conf[0] = ip[0]
    conf[1] = ip[1]
    conf[2] = ip[2]
    conf[3] = ip[3]

    back = reader_conf(reader, ctypes.c_ubyte(255), 168, conf, 0)
    if (back == 0):
        return True
    elif (back > 0):
        print('--- ! Reader conf status {}'.format(rfid_status_text(back)))
        return False
    else:
        print('--- ! Reader conf error {}'.format(back))
        print(rfid_error_text(ctypes.c_int(back)))
        return False


def rfid_reader_system_reset(reader):
    '''
    Perform a system reset (0x64) and save the configuration
    set in the EPPROM
    '''
    back = libfeisc.FEISC_0x64_SystemReset(reader, ctypes.c_ubyte(255))
    if (back == 0):
        return True
    elif (back > 0):
        print('--- ! Reader conf status {}'.format(rfid_status_text(back)))
        return False
    else:
        print('--- ! Reader conf error {}'.format(back))
        print(rfid_error_text(ctypes.c_int(back)))
        return False


def rfid_error_text(error_code):
    '''
    Print text for error code
    '''
    ucInfo = ctypes.create_string_buffer(300)
    libfeisc.FEISC_GetErrorText(error_code, ucInfo)
    return ucInfo.value


def rfid_status_text(status_code):
    '''
    Print text for status code
    '''
    ucInfo = ctypes.create_string_buffer(300)
    print('## checking status {}'.format(status_code))
    ucStatus = ctypes.c_ubyte(status_code)
    back = libfeisc.FEISC_GetStatusText(ucStatus, ucInfo)
    if (back == 0):
        return ucInfo.value
    else:
        print('Status check error, return value: {}'.format(back))
        print('{}'.format(rfid_error_text(back)))
        return None


def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


if __name__ == '__main__':
    import time
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="Command, 'config' to configure the reader ip address or 'read' to start reading RFID tags.", choices=['config', 'read'])
    parser.add_argument("--ip", help="the IP address of the reader.")
    parser.add_argument("--set-ip", help="the IP address to configure.")
    args = parser.parse_args()
    if args.command == 'config':
        print('Configuration')
        ip = args.ip
        set_ip = args.set_ip
        if ip is None or set_ip is None:
            print('Invalid usage, use --ip and --set-ip to change the IP configuration of the reader.')
            quit()
        # validate ip... basic
        if not validate_ip(ip):
            print('Invalid reader IP address {}'.format(ip))
            quit()
        if not validate_ip(set_ip):
            print('Invalid IP address {}'.format(set_ip))
            quit()

        # all good, connect to the reader
        print('Connecting to IP address {}'.format(ip))
        reader = rfid_connect(ip, PORT)
        conf = rfid_reader_lan_configuration_read(reader)
        print('Reader {} ready.'.format(reader))
        print('Reading reader info...')
        rfid_reader_info(reader)
        print('Changing IP address to {}'.format(set_ip))
        rfid_reader_lan_configuration_write(reader, conf, [int(x) for x in set_ip.split('.')])
        rfid_reader_system_reset(reader)
        print('All set, the IP address of the reader is now {}'.format(set_ip))
        quit()

    if args.command == 'read':
        ip = args.ip
        if ip is None or not validate_ip(ip):
            print('Invalid reader IP address.')
            quit()
        reader = rfid_connect(ip, PORT)
        print('Reader {} ready.'.format(reader))
        print('Reading reader info...')
        rfid_reader_info(reader)
        print('Press Ctrl-C to exit.')
        print('======== READING TAGS ============')
        try:
            while(True):
                found = rfid_read(reader)
                if (len(found)):
                    print('----------------------')
                    print('Found {} transponders:'.format(len(found)))
                    for f in found:
                        print('TR_TYPE = {} | DSFID = {} | IID = {}'.format(f.get('tr_type'), f.get('dsfid'), f.get('iid')))
                else:
                    print('No transponders in range.')
                time.sleep(.25)

        except KeyboardInterrupt:
            print('goodbye')
