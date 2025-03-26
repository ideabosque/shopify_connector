#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import shopify

from silvaengine_utility import Utility


class ShopifyConnector(object):
    def __init__(self, logger, **setting):
        self.logger = logger
        self.setting = setting
        self.session = shopify.Session(
            setting.get("shop_url"),
            setting.get("api_version"),
            setting.get("private_app_password"),
        )
        shopify.ShopifyResource.activate_session(self.session)

    def __del__(self):
        shopify.ShopifyResource.clear_session()

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, session):
        self._session = session

    def insert_update_product(self, product):
        _product = shopify.Product()
        _product.handle = product["sku"]
        _products = shopify.Product.find(handle=product["sku"])
        if len(_products) > 0:
            _product = _products[0]

        _product.attributes = dict(_product.attributes, **product["data"])
        success = _product.save()
        if success:
            results = Utility.json_loads(
                shopify.GraphQL().execute(
                    query="""mutation publishablePublishToCurrentChannel($id: ID!) {
                                publishablePublishToCurrentChannel(id: $id) {
                                    userErrors {
                                        field
                                        message
                                    }
                                }
                            }
                            """,
                    variables={"id": f"gid://shopify/Product/{_product.id}"},
                )
            )
            if (
                len(results["data"]["publishablePublishToCurrentChannel"]["userErrors"])
                > 0
            ):
                raise Exception(
                    results["data"]["publishablePublishToCurrentChannel"]["userErrors"][
                        0
                    ]["message"]
                )
            return
        raise Exception(_product.errors.full_messages())

    def insert_update_variant(self, variant):
        _products = shopify.Product.find(handle=variant["handle"])
        if len(_products) == 0:
            # raise Exception(
            #     f"Cannot find the product with the sku ({variant['handle']})."
            # )
            return

        options = []
        product_options = [
            option for option in _products[0].options if option.name != "Title"
        ]
        i = (
            0
            if len(product_options) == 0
            else max([option.position for option in product_options])
        )
        for k, v in variant["options"].items():
            _options = list(filter(lambda x: x.name == k, _products[0].options))
            if len(_options) > 0:
                variant["attributes"].update({f"option{_options[0].position}": v})
                continue

            i += 1
            option = shopify.Option(
                **{
                    "attributes": {
                        "product_id": _products[0].id,
                        "name": k,
                    }
                }
            )
            options.append(option)
            variant["attributes"].update({f"option{i}": v})

        if len(options) != 0:
            _products[0].options = options

        _variants = list(
            filter(
                lambda x: x.title != "Default Title",
                shopify.Variant.find(product_id=_products[0].id),
            )
        )
        _variant = shopify.Variant()
        _variant.product_id = _products[0].id
        for v in _variants:
            if v.sku == variant["sku"]:
                _variant = v
                break

        _variant.attributes = dict(_variant.attributes, **variant["attributes"])
        _variants.append(_variant)
        _products[0].variants = _variants
        success = _products[0].save()
        if success:
            return
        raise Exception(_products[0].errors.full_messages())

    # Find a product by attributes.
    def find_products_by_attributes(self, attributes):
        if not attributes:
            return None

        try:
            products = shopify.Product.find(**attributes)
            return products if products else None
        except Exception as e:
            self.logger.error(f"Error finding products: {str(e)}")
            return None

    def create_draft_order(self, customer, line_items, shipping_address={}):
        # Create new draft order
        draft_order = shopify.DraftOrder()

        # Set customer details
        draft_order.customer = customer

        # Add line items
        draft_order.line_items = line_items

        # Add shipping address if provided
        if shipping_address:
            draft_order.shipping_address = shipping_address

        # Save the draft order
        if draft_order.save():
            return draft_order.id
        else:
            raise Exception(draft_order.errors.full_messages())

    def find_customer_by_email(self, email):
        customers = shopify.Customer.find(email=email)
        if customers:
            for customer in customers:
                self.logger.info(
                    f"Customer Found: {customer.first_name} {customer.last_name} (Email: {customer.email})"
                )
            return customers
        else:
            self.logger.info("Customer not found.")
    def create_customer(self, first_name, last_name, email, phone, address):
        # Create a new customer
        customer = shopify.Customer()

        # Set customer details (you can add more attributes like tags, marketing_opt_in, etc.)
        customer.first_name = first_name
        customer.last_name = last_name
        customer.email = email
        customer.phone = phone
        customer.addresses = [address]

        # Save the customer
        if customer.save():
            self.logger.info(f"Customer created successfully! ID: {customer.id}")
            return customer
        else:
            self.logger.error(f"Failed to create customer: {customer.errors.full_messages()}")
            return None
