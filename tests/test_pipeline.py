from pathlib import Path

import pandas as pd

from data_engineering_project.pipeline import transform_data


def test_transform_data_normalizes_columns_and_amounts():
    df = pd.DataFrame(
        {
            "Order ID": [1, 2],
            "Amount": ["100.50", "abc"],
            "Status": [" Active ", "inactive"],
        }
    )

    result = transform_data(df)

    assert list(result.columns) == ["order_id", "amount", "status"]
    assert result["amount"].tolist() == [100.5, 0.0]
    assert result["status"].tolist() == ["active", "inactive"]
