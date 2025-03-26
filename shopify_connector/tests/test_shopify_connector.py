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

    @unittest.skip("demonstrating skipping")
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
        #     handle="1bolt-googpl2xl-blbk"
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

        document = """
            fragment ProductInfo on Product {
                id
                title
                description
                status
                vendor
                handle
            }

            query GetOneProduct($query: String!) {
                products(first: 1, query: $query) {
                    edges {
                        node { 
                            ...ProductInfo
                        }
                    } 
                }
            }
        """
        results = shopify.GraphQL().execute(
            query=document,
            variables={"query": "sku:mcc-gt-ghocas1017"},
            operation_name="GetOneProduct",
        )
        # results = shopify.GraphQL().execute(
        #     """{ products(first: 10, query: "sku:mcc-gt-ghocas1017") { edges { node { id title description status vendor handle } } } }"""
        # )
        # results = shopify.GraphQL().execute(
        #     "{ channels(first: 10) { edges { node { id name } } } }"
        # )
        # results = shopify.GraphQL().execute(
        #     "{ publications(first: 10) { edges { node { id name } } } }"
        # )

        # results = shopify.GraphQL().execute(
        #     query="""mutation publishablePublishToCurrentChannel($id: ID!) {
        #             publishablePublishToCurrentChannel(id: $id) {
        #                 userErrors {
        #                     field
        #                     message
        #                 }
        #             }
        #         }
        #         """,
        #     variables={
        #         "id": "gid://shopify/Product/2114471919673"
        #     },
        # )
        logger.info(Utility.json_dumps(Utility.json_loads(results)))

    @unittest.skip("demonstrating skipping")
    def test_create_customer(self):
        customer_data = {
            "email": "azrael_wang@aliyun.com",
            "first_name": "Jeffrey",
            "last_name": "Wang",
            "phone": "212-456-7890",
            "address": {
                "address1": "123 Main St",
                "address2": "",
                "city": "Irvine",
                "province_code": "CA",
                "province": "California",
                "zip": "96218",
                "country": "United States",
                "country_code": "US",
                "company": "Idea Bosque",
                "first_name": "Jeffrey",
                "last_name": "Wang",
                "phone": "212-456-7890",
            }
        }
        customer = self.shopify_connector.create_customer(**customer_data)
        logger.info(customer)
    
    @unittest.skip("demonstrating skipping")
    def test_find_customer_by_email(self):
        result = self.shopify_connector.find_customer_by_email("azrael_wang@aliyun.com")
        print(result[0])
        print(result[0].first_name)

    # @unittest.skip("demonstrating skipping")
    def test_find_products_by_attributes(self):
        attributes = {
            # "created_at_max": "2025-03-26T16:15:47-04:00",
            # "created_at_min": "2025-02-25T16:15:47-04:00",
            # "fields": "handle,id,image,options,product_type",
            "limit": 50,
            # "handle": "1bolt-googpl2xl-blbk",
            # "title": "Classic Bag Mitts",
            "product_type": "Boxing",
            "status": "active"
        }
        result = self.shopify_connector.find_products_by_attributes(attributes)
        print(result)
        for product in result:
            print(product.id)
            print(product.title)
            print(product.handle)
            print(product.product_type)
            print(product.status)

    @unittest.skip("demonstrating skipping")
    def test_create_draft_order(self):
        line_items = [{
            "quantity": 1,
            "variant_id": 44379840348217
        }]
        shipping_address = {
            "address1": "123 Main St",
            "address2": "",
            "city": "Irvine",
            "province_code": "CA",
            "zip": "96218",
            "country_code": "US",
            "company": "Idea Bosque",
            "first_name": "Jeffrey",
            "last_name": "Wang",
            "phone": "212-456-7890",
        }
        email = "azrael_wang@aliyun.com"
        customers = self.shopify_connector.find_customer_by_email("azrael_wang@aliyun.com")
        customer = {"id": customers[0].id}
        result = self.shopify_connector.create_draft_order(customer=customer, line_items=line_items, shipping_address=shipping_address)
        print(result)

if __name__ == "__main__":
    unittest.main()
