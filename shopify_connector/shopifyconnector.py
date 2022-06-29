#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from asyncio import Handle
from numpy import var

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
            return
        raise Exception(_product.errors.full_messages())

    def insert_update_variant(self, variant):
        _products = shopify.Product.find(handle=variant["handle"])
        if len(_products) == 0:
            raise Exception(
                f"Cannot find the product with the sku ({variant['handle']})."
            )

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
