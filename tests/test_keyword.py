from emailer_bot.email_monitor import EmailMonitor, IncomingEmail
from emailer_bot.config import IMAPConfig


def test_keyword_matching_whole_word_case_insensitive():
    monitor = EmailMonitor(IMAPConfig(host='x', port=993, username='u', password='p'))
    mail = IncomingEmail(uid='1', subject='BERT weekly update', from_email='a@b.com', body='No extra')
    assert monitor.has_keyword(mail, 'bert')


def test_keyword_does_not_match_substring():
    monitor = EmailMonitor(IMAPConfig(host='x', port=993, username='u', password='p'))
    mail = IncomingEmail(uid='2', subject='albert status', from_email='a@b.com', body='')
    assert not monitor.has_keyword(mail, 'bert')
