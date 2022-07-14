#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging, sys, unittest, os, traceback, boto3, shopify
from boto3.dynamodb.conditions import Key, Attr
from dotenv import load_dotenv
from silvaengine_utility import Utility


load_dotenv()
setting = {
    "shop_url": os.getenv("shop_url"),
    "api_version": os.getenv("api_version"),
    "private_app_password": os.getenv("private_app_password"),
    "region_name": os.getenv("region_name"),
    "aws_access_key_id": os.getenv("aws_access_key_id"),
    "aws_secret_access_key": os.getenv("aws_secret_access_key"),
}

sys.path.insert(0, "/var/www/projects/shopify_connector")

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()

from shopify_connector import ShopifyConnector


class ShopifyConnectorTest(unittest.TestCase):
    def setUp(self):
        self.shopify_connector = ShopifyConnector(logger, **setting)
        logger.info("Initiate ShopifyConnectorTest ...")

    def tearDown(self):
        logger.info("Destory ShopifyConnectorTest ...")

    # @unittest.skip("demonstrating skipping")
    def test_insert_update_product(self):
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=setting.get("region_name"),
            aws_access_key_id=setting.get("aws_access_key_id"),
            aws_secret_access_key=setting.get("aws_secret_access_key"),
        )

        response = dynamodb.Table("datamart_products_v2").query(
            KeyConditionExpression=Key("source").eq("ss3"),
            FilterExpression=Attr("updated_at").gt("2022-06-01T00:00:00+00"),
        )
        items = response["Items"]
        while "LastEvaluatedKey" in response:
            response = dynamodb.Table("datamart_products_v2").query(
                KeyConditionExpression=Key("source").eq("ss3"),
                ExclusiveStartKey=response["LastEvaluatedKey"],
                FilterExpression=Attr("updated_at").gt("2022-06-01T00:00:00+00"),
            )
            items.extend(response["Items"])

        if len(items) == 0:
            return

        for item in items:
            # if item["data"]["type"] == "configurable":
            #     tags = []
            #     categories = [
            #         "Category_"
            #         + category.replace("Default Category/Category/", "").split("/")[-1]
            #         for category in item["data"]["categories"]
            #         if category.find("Default Category/Category/") != -1
            #     ]
            #     tags.extend(categories)
            #     applications = [
            #         "Application_"
            #         + application.replace("Default Category/Application/", "").split(
            #             "/"
            #         )[-1]
            #         for application in item["data"]["applications"]
            #         if application.find("Default Category/Application/") != -1
            #     ]
            #     tags.extend(applications)
            #     tags.extend(
            #         [
            #             "Certifications_" + certification
            #             for certification in item["data"]["certifications"]
            #         ]
            #     )
            #     if item["data"]["country_of_origin"] in ("CN", "CHINA"):
            #         tags.append("Country of Origin_China")

            #     product = {
            #         "sku": item["sku"],
            #         "data": {
            #             "title": item["data"]["name"],
            #             "body_html": item["data"]["description"],
            #             "vendor": item["data"]["factory_code"],
            #             "tags": tags,
            #             "published_scope": "global"
            #         },
            #     }
            #     logger.info(product)
            #     self.shopify_connector.insert_update_product(product)

            if item["data"]["type"] == "simple":
                # logger.info(Utility.json_dumps(item))
                variant = {
                    "handle": item["data"]["variant_data"]["parent_product_sku"],
                    "options": {
                        k: v.split(" : ")[-1]
                        for k, v in item["data"]["variant_data"][
                            "variant_attributes"
                        ].items()
                    },
                    "attributes": {
                        "price": float(item["data"]["base_price"]),
                        "weight": float(item["data"]["tare_weight"]),
                        "weight_unit": item["data"]["uom"],
                    },
                    "sku": item["sku"],
                }
                logger.info(variant)
                self.shopify_connector.insert_update_variant(variant)
                # break

    @unittest.skip("demonstrating skipping")
    def test_get_products(self):
        # products = shopify.Product.find(
        #     # handle="aloe-barbadensis-powder-by-s-a-herbal-bioactives-llp"
        #     handle="93510-angel-11426"
        #     # handle="10002-yumfun-10763"
        # )
        # for product in products:
        #     logger.info(product.attributes)
        #     for option in product.options:
        #         logger.info(option.attributes)

        # products = shopify.Product.find(
        #     # handle="aloe-barbadensis-powder-by-s-a-herbal-bioactives-llp"
        #     handle="93510-angel-11426"
        # )
        # variants = shopify.Variant.find(product_id=products[0].id)
        # for variant in variants:
        #     logger.info(variant.attributes)

        # results = shopify.GraphQL().execute(
        #     "{ channels(first: 10) { edges { node { id name } } } }"
        # )
        # results = shopify.GraphQL().execute(
        #     "{ publications(first: 10) { edges { node { id name } } } }"
        # )

        results = shopify.GraphQL().execute(
            query="""mutation publishablePublishToCurrentChannel($id: ID!) {
                    publishablePublishToCurrentChannel(id: $id) {
                        userErrors {
                            field
                            message
                        }
                    }
                }
                """,
            variables={
                "id": "gid://shopify/Product/7433043214495"
            },
        )
        logger.info(Utility.json_dumps(Utility.json_loads(results)))


if __name__ == "__main__":
    unittest.main()
