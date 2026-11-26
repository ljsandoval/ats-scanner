from ats_scanner.filters import location_passes, title_passes
from ats_scanner.models import LocationFilter, TitleFilter


class TestTitleFilter:
    def test_empty_positive_passes_all_but_negatives(self):
        f = TitleFilter(negative=["intern"])
        assert title_passes("Data Engineer", f) is True
        assert title_passes("Data Engineering Intern", f) is False

    def test_positive_required_when_present(self):
        f = TitleFilter(positive=["data engineer"])
        assert title_passes("Senior Data Engineer", f) is True
        assert title_passes("Product Manager", f) is False

    def test_negative_beats_positive(self):
        f = TitleFilter(positive=["engineer"], negative=["manager"])
        assert title_passes("Engineering Manager", f) is False

    def test_case_insensitive(self):
        f = TitleFilter(positive=["DATA engineer"])
        assert title_passes("senior data ENGINEER", f) is True


class TestLocationFilter:
    def test_empty_location_passes(self):
        f = LocationFilter(allow=["Remote"], block=["India"])
        assert location_passes("", f) is True
        assert location_passes("   ", f) is True

    def test_always_allow_beats_block(self):
        f = LocationFilter(always_allow=["Portland"], block=["India"])
        # multi-location posting naming home region wins
        assert location_passes("Remote, Portland or India", f) is True

    def test_block_rejects(self):
        f = LocationFilter(allow=["Remote"], block=["India"])
        assert location_passes("Bengaluru, India", f) is False

    def test_allow_required_when_present(self):
        f = LocationFilter(allow=["Remote", "United States"])
        assert location_passes("Remote (US)", f) is True
        assert location_passes("Toronto, Canada", f) is False

    def test_no_allow_list_passes_after_block(self):
        f = LocationFilter(block=["India"])
        assert location_passes("Anywhere", f) is True
