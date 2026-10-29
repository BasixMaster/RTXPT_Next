import unittest,codecs
from presentmon_log import decode_log,reported_loss

class PresentMonLogTests(unittest.TestCase):
    def test_utf8_loss(self):self.assertTrue(reported_loss(b'warning: ETW events were lost during capture.\n'))
    def test_utf8_bom(self):self.assertTrue(reported_loss(codecs.BOM_UTF8+b'ETW events were lost'))
    def test_utf16le_native_regression(self):
        raw=codecs.BOM_UTF16_LE+'warning: ETW events were lost during capture.'.encode('utf-16-le')
        self.assertTrue(reported_loss(raw))
        self.assertNotIn('ETW events were lost',raw.decode('utf-8',errors='replace'))
    def test_utf16be(self):self.assertTrue(reported_loss(codecs.BOM_UTF16_BE+'ETW events were lost'.encode('utf-16-be')))
    def test_recording_messages_are_not_loss(self):
        for codec in ['utf-8','utf-16']:
            self.assertFalse(reported_loss('Started recording.\nStopped recording.\n'.encode(codec)))
    def test_unicode_text_preserved(self):self.assertEqual(decode_log('Début\n'.encode('utf-16')),'Début\n')
    def test_empty(self):self.assertFalse(reported_loss(b''))

if __name__=='__main__':unittest.main()
