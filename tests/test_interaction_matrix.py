import pandas as pd

from daxlab.research.interaction_matrix import compose_masks, summarize_mask


def test_components_remain_visible_and_combined_is_intersection():
    frame = pd.DataFrame({"r": [1.0, -1.0, 2.0], "a": [1, 1, 0], "b": [1, 0, 1]})
    masks = compose_masks(
        frame,
        {
            "A": lambda x: x["a"] == 1,
            "B": lambda x: x["b"] == 1,
        },
    )
    assert masks["A"].tolist() == [True, True, False]
    assert masks["B"].tolist() == [True, False, True]
    assert masks["combined"].tolist() == [True, False, False]


def test_summary_reports_selected_trade_metrics():
    frame = pd.DataFrame({"r": [1.0, -1.0, 2.0]})
    result = summarize_mask(frame, pd.Series([True, False, True]), name="x")
    assert result.trades == 2
    assert result.return_r == 3.0
    assert result.win_rate == 1.0
