# What Women Want dashboard API

## What does this API do?

This API is used for retrieving campaign responses from BigQuery to display in a dashboard.

## Where is the URL?

https://www-dashboard-api-dot-deft-stratum-290216.uc.r.appspot.com/

## Continuous integration

This API is built automatically by Github actions.

The Docker container is pushed to Google Container Registry.

Then it is deployed to Google App Engine using a Flex environment (see `app.yaml`).
