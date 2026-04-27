import pandas as pd
import numpy as np
import random


def generate_massive_audit_data(rows=10000):
    countries = ['USA', 'UK', 'UAE', 'Cayman Islands', 'Russia', 'Switzerland']
    flags = ['High Risk', 'Low Risk', 'PEP Match', 'None']

    data = {
        'transaction_id': [f"TXN-{100000 + i}" for i in range(rows)],
        'amount': np.round(np.random.uniform(500, 1000000, size=rows), 2),
        'country': [random.choice(countries) for _ in range(rows)],
        'risk_score': [random.choice(flags) for _ in range(rows)],
        'timestamp': pd.date_range(start='2026-01-01', periods=rows, freq='min')
    }

    df = pd.DataFrame(data)
    df.to_csv('data/massive_stress_test.csv', index=False)
    print(f"✅ Success: Generated {rows} transactions in 'data/massive_stress_test.csv'")


if __name__ == "__main__":
    generate_massive_audit_data(10000)