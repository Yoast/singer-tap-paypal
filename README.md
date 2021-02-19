# tap-paypal

This is a [Singer](https://singer.io) tap that produces JSON-formatted data
following the [Singer
spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This tap:

- Pulls raw data from [PayPal](https://developer.paypal.com/docs/api/overview/)
- Extracts the following resources:
  - [Transactions](https://developer.paypal.com/docs/api/transaction-search/v1)
- Outputs the schema for each resource
- Incrementally pulls data based on the input state

### Step 1: Create a OAuth key in PayPal

1. [Log in to the Developer Dashboard](https://www.paypal.com/signin?returnUri=https%3A%2F%2Fdeveloper.paypal.com%2Fdeveloper%2Fapplications) with your PayPal account.
2. Under the DASHBOARD menu, select My Apps & Credentials.
3. Make sure you're on the Live tab if you want to use the Live environment, to get the Live API credentials.
4. Under the App Name column, select Default Application, which PayPal creates with a new Developer Dashboard account. Select Create App if you don't see the default app.

### Step 2: Configure

Create a file called `paypal_config.json` in your working directory, following [config.json.example](config.json.example). The required parameters are the `client_id` and `secret`. The sandbox parameter determines whether to use the sandbox or live environment.

This requires a `state.json` file to let the tap know from when to retrieve data. For example:
```
{
  "bookmarks": {
    "paypal_transactions": {
      "start_date": "2021-01-01T00:00:00+0000"
    }
  }
}
```
Will replicate transaction data from 2021-01-01.

### Step 3: Install and Run

Create a virtual Python environment for this tap. This tap has been tested with Python 3.7, 3.8 and 3.9 and might run on future versions without problems.
```
python -m venv singer-paypal
singer-paypal/bin/python -m pip install --upgrade pip
singer-paypal/bin/pip install git+https://github.com/Yoast/singer-tap-paypal.git
```

This tap can be tested by piping the data to a local JSON target. For example:

Create a virtual Python environment with `singer-json`
```
python -m venv singer-json
singer-json/bin/python -m pip install --upgrade pip
singer-json/bin/pip install target-json
```

Test the tap:

```
singer-paypal/bin/tap-paypal --state state.json -c paypal_config.json | singer-json/bin/target-json >> state_result.json
```

Copyright &copy; 2021 Yoast