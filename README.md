# REPAIR Model

The Risk-controlled Expansion Planning with Distributed Resources (REPAIR) is an innovative tool to support decisions around utility grid planning to prevent and mitigate the impact of outages caused by routine equipment failures (reliability) or by extreme events (resilience), such as storms, earthquakes or wildfires that long term interruption of service.

REPAIR is a risk-based optimization and decision-making model allowing informed and transparent “cost vs risk” decisions regarding infrastructural planning of electric utilities. The model considers long-term resilience and reliability planning strategies that rely on traditional infrastructure upgrade (e.g. circuit hardening, reinforcement, new substations, etc.) or new investment alternatives, such as DERs.

This code is also available to use as an [online tool](https://repairtool.lbl.gov/).

### Prerequisites

For using this package, you need to use Python 3.8+, along with the libraries
specified in requirements.txt.

To run the problem, a MILP solver needs to be installed. We recommend CBC, which is
free to use.


### Installing


For using this module, there are some python libraries that need to be installed. This can be done by cloning the project and running on the main folder:
```
pip install pipenv
pipenv shell
pipenv install
```

otherwise, by using the requirements file:

```
pip install -r requirements.txt
```


CBC can be installed for all platforms. For installation instructions, check the [github repository](https://github.com/coin-or/Cbc). The solver can be modified by modifying line 31 in run.py.


## Running

You can run the model by executing the following command in the main folder:

```
python run.py
```

which will output files in solutions folder.

## Modifying Dataset

In order to modify the data, there is a detailed set of files that can be modified, which are present in the example_case folder. By modifying this values, or by using a different folder entirely, the inputs from this model can be changed. The [online tool](https://repairtool.lbl.gov/) also might be an easier choice in order to do this.


### Research

The mathematical models to support repair can be found in open access journal publications.

Publications:
- [Paper with final methodology and demonstration](http://arxiv.org/abs/2209.14460)
- [Previous publication](https://www.mdpi.com/1996-1073/14/24/8482)

## Authors
Project Team

* **Miguel Heleno** - *Project PI* - [Miguel Heleno](miguelheleno@lbl.gov)
* **Alexandre Moreira** - *Project team* - [Alexandre Moreira](amoreira@lbl.gov)
* **Alan Valenzuela** - *Project team* - [Alan Valenzuela](alanvalenzuela@lbl.gov)
* **Joe Eto** - *Project team* - [Joe Eto](jheto@lbl.gov)

Industry Partners:
REPAIR was developed in partnership with Commonwealth Edison.

![alt text](others/lbnl.png)
![alt text](others/comed.jpeg)


## Sponsors

The REPAIR model was sponsored by the US Department of Energy (DOE) through the Microgrids R&D and the Advanced Grid Modeling Programs from the Office of Electricity.

![alt text](others/usenergy.jpeg)
