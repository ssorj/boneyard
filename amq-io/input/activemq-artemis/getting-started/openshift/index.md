# Getting started with ActiveMQ Artemis on OpenShift

This article guides you through the steps to run ActiveMQ Artemis on
OpenShift.

## Prerequisites

* Access to a running instance of OpenShift.
  [Minishift](https://docs.okd.io/latest/minishift/getting-started/index.html)
  is one way to do this in your local environment.

## Steps

1. Log in to your OpenShift instance.  Use the `oc login` command
   provided by the OpenShift web interface under .

        oc login <>

1. Create a new project in OpenShift.

        oc new-project

1. Get the example project source from GitHub.

1. Apply the project OpenShift templates.

        oc apply -f templates/

1. Deploy the broker.

        oc new-app --template=activemq-artemis

1. Deploy the message producer.

        oc new-app --template=message-producer

1. Deploy the message consumer.

        oc new-app --template=message-consumer

1. See the result in your browser.

;; ## The message producer

;; ## The message consumer
