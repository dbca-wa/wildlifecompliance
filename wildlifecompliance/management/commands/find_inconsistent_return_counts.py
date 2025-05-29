from django.core.management.base import BaseCommand
from wildlifecompliance.components.returns.models import ReturnRow, ReturnActivity
import logging
from datetime import datetime
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Print a report of all return tables with totals not conistent with existing rows'

    def handle(self, *args, **options):
        multiple_stock_rows = [] #returns sometimes have multiple stock rows - stocks cannot be added via return interface
        no_stock_rows = []
        out_of_order_before_stock_rows = []
        bad_date_format = []

        #get return tables via return rows (not directly)
        return_row_tables = ReturnRow.objects.distinct("return_table")
        all_return_rows = ReturnRow.objects

        #iterate through each table
        for table_return_row in return_row_tables:
            bad_date = False
            return_table = table_return_row.return_table
            return_rows = all_return_rows.filter(return_table=return_table)
            #get num of stock - report if multiple stock
            stock_rows = return_rows.filter(data__activity=ReturnActivity.TYPE_IN_STOCK)
            if stock_rows.count() > 1:
                multiple_stock_rows.append(return_table.id)
                msg = "Return Table {} has multiple stock rows".format(return_table.id)
                print(msg)
                logger.info(msg)
                
                #get all rows with doa after respective stock
                stock_return_row_json = list(stock_rows.values_list('data',flat=True))
                stock_row_dates = list(stock_rows.values_list("data__doa", flat=True))
                for i in range(len(stock_row_dates)):
                    try:
                        stock_row_dates[i] = datetime.strptime(stock_row_dates[i], '%d/%m/%Y').date()
                    except:
                        bad_date = True
                        break
                if bad_date:
                    bad_date_format.append(return_table.id)
                    msg = "Return Table {} has at least one row with an incorrect date value/format".format(return_table.id)
                    print(msg)
                    logger.info(msg)
                    continue
                
                stock_row_dates.sort()
                #get return rows
                non_stock_return_row_json = list(return_rows.exclude(data__activity=ReturnActivity.TYPE_IN_STOCK).values_list('data',flat=True))
                #because of how the values are stored, we have to order each return row data entry outside of ORM with the json values

                #TODO group activities to before all stock dates and in to groups before each stock date - get the presented total and the actual total

                for i in non_stock_return_row_json:
                    try:
                        doa = datetime.strptime(i["doa"], '%d/%m/%Y').date()
                    except:
                        bad_date = True
                        break
                    if doa < stock_row_dates[0]:
                        out_of_order_before_stock_rows.append(return_table.id)
                        msg = "Return Table {} has activities reported before stock activities".format(return_table.id)
                        print(msg)
                        logger.info(msg)
                if bad_date:
                    bad_date_format.append(return_table.id)
                    msg = "Return Table {} has at least one row with an incorrect date value/format".format(return_table.id)
                    print(msg)
                    logger.info(msg)
                    continue

            elif stock_rows == 0:
                no_stock_rows.append(return_table.id)
                msg = "Return Table {} has no stock".format(return_table.id)
                print(msg)
                logger.info(msg)
                    

        
        #end report
        msg = "\n\n{} return tables have multiple stock rows".format(len(multiple_stock_rows))
        print(msg)
        logger.info(msg)
        print(multiple_stock_rows)
        logger.info(multiple_stock_rows)

        msg = "\n\n{} return tables have no stock row".format(len(no_stock_rows))
        print(msg)
        logger.info(msg)
        print(no_stock_rows)
        logger.info(no_stock_rows)

        msg = "\n\n{} return tables have activities prior to stock row activities".format(len(out_of_order_before_stock_rows))
        print(msg)
        logger.info(msg)
        print(out_of_order_before_stock_rows)
        logger.info(out_of_order_before_stock_rows)

        msg = "\n\n{} return tables have rows with incorrect date of activity values/formats".format(len(bad_date_format))
        print(msg)
        logger.info(msg)
        print(bad_date_format)
        logger.info(bad_date_format)