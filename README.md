# Let's Write a Python Quote Bot!

This repository will get you started with building a quote bot in Python. It's meant to be used along with the [Learning Lab](https://lab.github.com) intro to Python.

When complete, you'll be able to grab random quotes from the command line, like this:

> **$** python get-quote.py
> 
> Keep it logically awesome
> 
> **$** python get-quote.py
> 
> Speak like a human

## Start the Tutorial

You can find your next step in [this repo's issues](../../issues/)!

## Staff Cost Modelling Scenario Tool

This repo now includes a Streamlit scenario modeller to test vacancy start dates and compare spend variance against budget.

### Run it locally

```bash
pip install streamlit pandas
streamlit run staff_cost_model.py
```

### What it does

- Define a budget period and budget amount.
- Add/edit vacancies with salary, on-cost rate, and two dates:
  - **Budgeted Start** (baseline)
  - **Scenario Start** (what-if)
- See total vacancy costs and variance versus budget instantly.
