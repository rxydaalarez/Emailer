from emailer_bot.onedrive_client import ResearchFile
from emailer_bot.workflow import _extract_scored_points


def test_extract_scored_points_from_mixed_files():
    files = [
        ResearchFile(name='notes.txt', content='2025-01-01 score: 0.4'),
        ResearchFile(name='history.csv', content='date,score\n2025-01-02,0.6'),
        ResearchFile(name='signal.json', content='[{"date":"2025-01-03","score":0.8}]'),
    ]

    points = _extract_scored_points(files)
    assert len(points) == 3
    assert [round(p[1], 1) for p in points] == [0.4, 0.6, 0.8]
