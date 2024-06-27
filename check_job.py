import json
import time

from baseopensdk import BaseClient, JSON
from baseopensdk.api.base.v1 import *
import requests as re

from exceptions import FieldError, PersonalBaseTokenError


def test404(url):
  code = re.get(url).status_code
  return code == 200


def check_job(baseId, tableId, personalBaseToken, fieldToCheck):
  # 构建client
  client: BaseClient = BaseClient.builder() \
      .app_token(baseId) \
      .personal_base_token(personalBaseToken) \
      .build()

  field_request = ListAppTableFieldRequest.builder() \
      .page_size(100) \
      .table_id(tableId) \
      .build()

  field_response = client.base.v1.app_table_field.list(field_request)
  field_list = json.loads(JSON.marshal(field_response.data))
  if field_list['items'] == None:
    raise PersonalBaseTokenError("授权码错误")
  target_field = ''
  for field in field_list['items']:
    if field['field_id'] == fieldToCheck:
      target_field = field['field_name']
      break
  if target_field == '':
    pass  # 异常
  page_token = None

  while True:
    if page_token is None:
      records_request = ListAppTableRecordRequest.builder().field_names(
        '["' + target_field + '"]').page_size(500).table_id(tableId).build()
    else:
      records_request = ListAppTableRecordRequest.builder().field_names(
        '["' + target_field +
        '"]').page_size(500).table_id(tableId).page_token(page_token).build()
    records_response = client.base.v1.app_table_record.list(records_request)
    records = json.loads(JSON.marshal(records_response.data))
    update_data = []
    for record in records['items']:
      try:
        temp = AppTableRecord().builder().record_id(
          record['record_id']).fields({
            "链接可用性":
            "可用" if test404(record['fields'][target_field]['link']) else "不可用"
          }).build()
        update_data.append(temp)
      except:
        raise FieldError("待检查列选择错误，请选择超链接类型的列")
    batch_update_request = BatchUpdateAppTableRecordRequest.builder().table_id(
      tableId).request_body(
        BatchUpdateAppTableRecordRequestBody().builder().records(
          update_data).build()).build()
    batch_update_response = client.base.v1.app_table_record.batch_update(
      batch_update_request)
    if not records['has_more']:
      break
    page_token = records['page_token']
    time.sleep(1)  # 防止请求过快，超出频率限制
