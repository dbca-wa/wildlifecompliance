from django.core.management.base import BaseCommand
from wildlifecompliance.components.returns.models import ReturnRow, ReturnActivity
import logging
from datetime import datetime
import uuid
import xlsxwriter
from django.conf import settings
from wildlifecompliance.components.emails.emails import TemplateEmailBase
from wildlifecompliance.settings import NOTIFICATION_EMAIL

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Print a report of all return tables with totals not conistent with existing rows'

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            dest='id'
        )

    def create_report_sheet(self, worksheet, sheet_name, sheet_info, sheet_rows):

        col = 0
        row = 0
        row_header = ["Return Table Id", "Return Table Species", "Return Id"]

        worksheet.write(row, col, sheet_name)
        row += 1
        worksheet.write(row, col, sheet_info)
        row += 1

        for header_col in row_header:
            worksheet.write(row, col, header_col)
            col += 1
        row += 1
        col = 0

        for sheet_row in sheet_rows:
            for sheet_col in sheet_row:
                worksheet.write(row, col, sheet_col)
                col += 1
            row += 1
            col = 0


    def handle(self, *args, **options):
        multiple_stock_rows = [] #returns sometimes have multiple stock rows - stocks cannot be added via return interface
        multiple_stock_rows_with_same_dates = []
        no_stock_rows = []
        out_of_order_before_stock_rows = []
        bad_date_format = []
        incorrect_totals = []
        incorrect_totals_with_multiple_stocks = []
        incorrect_totals_out_of_order = []
        incorrect_totals_regardless_ordering = []
        incorrect_totals_without_ordering_correct_with_ordering = []

        if 'id' in options and options['id']:
            return_row_tables = ReturnRow.objects.filter(return_table_id=options['id']).distinct("return_table")
            all_return_rows = ReturnRow.objects.filter(return_table_id=options['id'])
        else:
            #get return tables via return rows (not directly)
            return_row_tables = ReturnRow.objects.distinct("return_table")
            all_return_rows = ReturnRow.objects

        #iterate through each table
        count = 0
        for table_return_row in return_row_tables:
            count += 1
            bad_date = False
            return_table = table_return_row.return_table
            return_rows = all_return_rows.filter(return_table=return_table)
            #get num of stock - report if multiple stock
            stock_rows = return_rows.filter(data__activity=ReturnActivity.TYPE_IN_STOCK)

            if stock_rows.count() > 1:
                multiple_stock_rows.append([return_table.id, return_table.name, return_table.ret_id])
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
                    bad_date_format.append([return_table.id, return_table.name, return_table.ret_id])
                    msg = "Return Table {} has at least one row with an incorrect date value/format".format(return_table.id)
                    print(msg)
                    logger.info(msg)
                    continue
                
                stock_row_dates.sort()

                same_dates = False
                if len(stock_row_dates) < len(list(set(stock_row_dates))):
                    multiple_stock_rows_with_same_dates.append([return_table.id, return_table.name, return_table.ret_id])
                    msg = "Return Table {} has multiple stock rows with the same activity dates".format(return_table.id)
                    print(msg)
                    logger.info(msg)
                    same_dates = True

                stock_return_row_json_temp = []
                skip_for_same_date = False
                for date in stock_row_dates:
                    for row in stock_return_row_json:
                        row_date = datetime.strptime(row["doa"], '%d/%m/%Y').date()
                        if row_date == date:
                            if same_dates and skip_for_same_date:
                                skip_for_same_date = False
                                continue
                            elif same_dates:
                                skip_for_same_date = True
                            stock_return_row_json_temp.append(row)
                            break
                stock_return_row_json = stock_return_row_json_temp            

                #get return rows
                non_stock_return_row_json = list(return_rows.exclude(data__activity=ReturnActivity.TYPE_IN_STOCK).values_list('data',flat=True))
                #because of how the values are stored, we have to order each return row data entry outside of ORM with the json values

                #group activities to before all stock dates and in to groups before each stock date - get the presented total and the actual total
                stock_groups = [[]]*len(stock_row_dates)
                
                for i in range(len(stock_groups)):
                    stock_groups[i].append(stock_return_row_json[i])

                for row in non_stock_return_row_json:
                    try:
                        doa = datetime.strptime(row["doa"], '%d/%m/%Y').date()
                    except:
                        bad_date = True
                        break
                    if doa < stock_row_dates[0]:
                        out_of_order_before_stock_rows.append([return_table.id, return_table.name, return_table.ret_id])
                        msg = "Return Table {} has activities reported before stock activities".format(return_table.id)
                        print(msg)
                        logger.info(msg)
                    else:
                        for i in range(len(stock_row_dates)):
                            group_index = 0
                            if doa >= stock_row_dates[i]:
                                group_index = i
                        stock_groups[group_index].append(row)

                if bad_date:
                    bad_date_format.append([return_table.id, return_table.name, return_table.ret_id])
                    msg = "Return Table {} has at least one row with an incorrect date value/format".format(return_table.id)
                    print(msg)
                    logger.info(msg)
                    continue

                #for each stock group, check if the counts are consistent
                bad_date = False
                recorded = False
                for stock_group in stock_groups:
                    stock_row = stock_group[0]
                    initial_total = stock_row["total"]

                    #get latest doa from remaining rows (if multiple, order those by date added)
                    latest = None
                    in_total = 0
                    out_total = 0
                    for i in range(1,len(stock_group)):
                        if not latest:
                            latest = stock_group[i]
                        elif latest["doa"] == stock_group[i]["doa"]:
                            if stock_group[i]["date"] > latest["date"]:
                                latest = stock_group[i]
                        else:
                            try:
                                latest_doa = datetime.strptime(latest["doa"], '%d/%m/%Y').date()
                                doa = datetime.strptime(stock_group[i]["doa"], '%d/%m/%Y').date()
                            except:
                                bad_date = True
                                break
                            if doa > latest_doa:
                                latest = stock_group[i]
                        if stock_group[i]["activity"].startswith("in_"):
                            in_total += int(stock_group[i]["qty"])
                        if stock_group[i]["activity"].startswith("out_"):
                            out_total += int(stock_group[i]["qty"])

                    if bad_date:
                        break
                    
                    if latest:
                        latest_total = latest["total"]
                    else: 
                        latest_total = initial_total
                    correct_total = initial_total + in_total - out_total

                    if latest_total != correct_total and not recorded:
                        incorrect_totals_with_multiple_stocks.append([return_table.id, return_table.name, return_table.ret_id])
                        msg = "Return Table {} has an incorrect total and multiple stock rows".format(return_table.id)
                        print(msg)
                        logger.info(msg)
                        recorded = True

                if bad_date:
                    bad_date_format.append([return_table.id, return_table.name, return_table.ret_id])
                    msg = "Return Table {} has at least one row with an incorrect date value/format".format(return_table.id)
                    print(msg)
                    logger.info(msg)
                    continue
                
            elif stock_rows.count() == 0:
                no_stock_rows.append([return_table.id, return_table.name, return_table.ret_id])
                msg = "Return Table {} has no stock".format(return_table.id)
                print(msg)
                logger.info(msg)
            
            #we count again, without concern for stock grouping
            if stock_rows.count() > 0:
                stock_return_row_json = list(return_rows.filter(data__activity=ReturnActivity.TYPE_IN_STOCK).values('id','data'))
                non_stock_return_row_json = list(return_rows.exclude(data__activity=ReturnActivity.TYPE_IN_STOCK).values('id','data'))

                return_table_rows = stock_return_row_json + non_stock_return_row_json

                stock_row = return_table_rows[0]
                initial_total = stock_row["data"]["total"]

                try:
                    stock_row_date = datetime.strptime(stock_row["data"]["doa"], '%d/%m/%Y').date()
                except:
                    bad_date = True
                    continue

                if bad_date:
                    bad_date_format.append([return_table.id, return_table.name, return_table.ret_id])
                    msg = "Return Table {} has at least one row with an incorrect date value/format".format(return_table.id)
                    print(msg)
                    logger.info(msg)
                    continue

                #get latest doa from remaining rows (if multiple, order those by date added)
                latest = None
                latest_added = None
                in_total = 0
                out_total = 0
                out_of_order = False
                for i in range(1,len(return_table_rows)):
                    try:
                        doa = datetime.strptime(return_table_rows[i]["data"]["doa"], '%d/%m/%Y').date()
                    except:
                        bad_date = True
                        break

                    if doa < stock_row_date and not(stock_rows.count() > 1):
                        out_of_order_before_stock_rows.append([return_table.id, return_table.name, return_table.ret_id])
                        msg = "Return Table {} has activities reported before stock activities".format(return_table.id)
                        print(msg)
                        logger.info(msg)
                        out_of_order = True
                        #continue

                    if not latest:
                        latest = return_table_rows[i]
                    elif latest["data"]["doa"] == return_table_rows[i]["data"]["doa"]:
                        if return_table_rows[i]["data"]["date"] > latest["data"]["date"]:
                            latest = return_table_rows[i]
                    else:
                        try:
                            latest_doa = datetime.strptime(latest["data"]["doa"], '%d/%m/%Y').date()
                        except:
                            bad_date = True
                            break
                        if doa > latest_doa:
                            latest = return_table_rows[i]

                    if not latest_added:
                        latest_added = return_table_rows[i]
                
                    elif int(latest_added["data"]["date"]) < int(return_table_rows[i]["data"]["date"]):
                        latest_added = return_table_rows[i]
                    
                    if return_table_rows[i]["data"]["activity"].startswith("in_"):
                        in_total += int(return_table_rows[i]["data"]["qty"])
                    if return_table_rows[i]["data"]["activity"].startswith("out_"):
                        out_total += int(return_table_rows[i]["data"]["qty"])                        

                if bad_date:
                    bad_date_format.append([return_table.id, return_table.name, return_table.ret_id])
                    msg = "Return Table {} has at least one row with an incorrect date value/format".format(return_table.id)
                    print(msg)
                    logger.info(msg)
                    continue

                if latest:
                    latest_total = latest["data"]["total"]
                else: 
                    latest_total = initial_total

                if latest_added:
                    latest_added_total = latest_added["data"]["total"]
                else: 
                    latest_added_total = initial_total
                
                correct_total = initial_total + in_total - out_total
                
                correct_by_doa = False
                if latest_total != correct_total:
                    print("Initial (stock) total {}, total in {}, total out {}".format(initial_total,in_total,out_total))
                    print("Correct Total:",correct_total)
                    print("Reported Total (when ordered by activity date):",latest_total)
                    if out_of_order:
                        incorrect_totals_out_of_order.append([return_table.id, return_table.name, return_table.ret_id])
                        msg = "Return Table {} has an incorrect total with activities prior to stock (still counted) when ordered by activity date".format(return_table.id)
                        print(msg)
                        logger.info(msg)   
                    else:
                        incorrect_totals.append([return_table.id, return_table.name, return_table.ret_id])
                        msg = "Return Table {} has an incorrect total when ordered by activity date".format(return_table.id)
                        print(msg)
                        logger.info(msg)
                else:
                    correct_by_doa = True

                if latest_added_total != correct_total:
                    if correct_by_doa:
                        incorrect_totals_without_ordering_correct_with_ordering.append([return_table.id, return_table.name, return_table.ret_id])
                        msg = "Return Table {} has an incorrect total when ordered by when added, but correct when ordered by doa".format(return_table.id)
                        print(msg)
                        logger.info(msg)
                    else:
                        print("Initial (stock) total {}, total in {}, total out {}".format(initial_total,in_total,out_total))
                        print("Correct Total:",correct_total)
                        print("Reported Total (when ordered by record added date):",latest_added_total)
                        incorrect_totals_regardless_ordering.append([return_table.id, return_table.name, return_table.ret_id])
                        msg = "Return Table {} has an incorrect total".format(return_table.id)
                        print(msg)
                        logger.info(msg)
                        print(return_table_rows)
        
        #report
        print("\n\nREPORT")
        print("--------------------------------------------------------------------------------")

        excel_file = str(settings.BASE_DIR)+'/tmp/{}_{}_{}.xlsx'.format("returns_report",uuid.uuid4(),int(datetime.now().timestamp()*100000))
        workbook = xlsxwriter.Workbook(excel_file) 
        worksheet_titles = [
            "Incorrect added order".format(len(incorrect_totals_regardless_ordering)),
            "Incorrect activity date order".format(len(incorrect_totals)),
            "Bad date format".format(len(bad_date_format)),
            "Incorrect many stock rows".format(len(incorrect_totals_with_multiple_stocks)),
            "Incorrect pre-stock activity".format(len(incorrect_totals_out_of_order)),
            "No stock row".format(len(no_stock_rows)),
            "Many stock rows same date".format(len(multiple_stock_rows_with_same_dates)),
            "Many stock rows".format(len(multiple_stock_rows)),
        ]
        worksheet_info = [
            "The totals for these return tables are incorrect even when disregarding multiple stock rows and incorrect activity date orders. These rows are ordered by whenever they had been added.",
            "The total may still be correct when the activity date is disregarded or corrected. But this error at least means that the activity dates provided do not match what should be expected.",
            "A bad date renders the return table unorderable. No further information will be available until this is remedied.",
            "The total may still be correct when the activity date is disregarded or corrected, as well as if the extra stock rows were to be corrected or counted as any other row.",
            "The total may still be correct when the activity date is disregarded or corrected. This report counts activities with dates recorded prior to stock (where all activities should be after stock).",
            "All return tables should have at least one stock row. No further information regarding this return row will be available until this is remedied.",
            "If a return table has multiple stock rows and those rows have the same activity date, there is no way to reliably determine what order the activities should be counted if relying on the date of activity.",
            "A return table should only have one initial stock row. Multiple stock rows may cause issues with counts.",
        ]
        worksheet_data = [
            incorrect_totals_regardless_ordering,
            incorrect_totals,
            bad_date_format,
            incorrect_totals_with_multiple_stocks,
            incorrect_totals_out_of_order,
            no_stock_rows,
            multiple_stock_rows_with_same_dates,
            multiple_stock_rows,
        ]
        
        for i in range(len(worksheet_titles)):
            worksheet = workbook.add_worksheet(worksheet_titles[i])
            self.create_report_sheet(worksheet, worksheet_titles[i], worksheet_info[i], worksheet_data[i])

        workbook.close() 

        #email report
        attachments = []
        attachments.append(excel_file)
        #email to user
        email = TemplateEmailBase(
            subject='Attached: Return Totals Report', 
            html_template='wildlifecompliance/components/returns/templates/wildlifecompliance/emails/send_return_count_report.html',
            txt_template='wildlifecompliance/components/returns/templates/wildlifecompliance/emails/send_return_count_report.txt',
        )
        to_address = NOTIFICATION_EMAIL
        # Send email
        email.send(to_address, attachments=attachments)

        msg = "\n\n{} return tables have multiple stock rows".format(len(multiple_stock_rows))
        print(msg)
        logger.info(msg)
        print(multiple_stock_rows)
        logger.info(multiple_stock_rows)
        exp = "\nA return table should only have one initial stock row. Multiple stock rows may cause issues with counts."
        print(exp)
        logger.info(exp)
        print("--------------------------------------------------------------------------------")

        msg = "\n\n{} return tables have multiple stock rows where some have the same activity dates".format(len(multiple_stock_rows_with_same_dates))
        print(msg)
        logger.info(msg)
        print(multiple_stock_rows_with_same_dates)
        logger.info(multiple_stock_rows_with_same_dates)
        exp = "\nIf a return table has multiple stock rows and those rows have the same activity date, there is no way to reliably determine what order the activities should be counted if relying on the date of activity."
        print(exp)
        logger.info(exp)
        print("--------------------------------------------------------------------------------")

        msg = "\n\n{} return tables have no stock row".format(len(no_stock_rows))
        print(msg)
        logger.info(msg)
        print(no_stock_rows)
        logger.info(no_stock_rows)
        exp = "\nAll return tables should have at least one stock row. No further information regarding this return row will be available until this is remedied."
        print(exp)
        logger.info(exp)
        print("--------------------------------------------------------------------------------")

        msg = "\n\n{} return tables have activities prior to stock row activities".format(len(out_of_order_before_stock_rows))
        print(msg)
        logger.info(msg)
        print(out_of_order_before_stock_rows)
        logger.info(out_of_order_before_stock_rows)
        exp = "\nReturn table has recorded activities with date prior to stock date. These activities cannot be counted when determining the correct total as ordered by activity date (only recorded date)."
        print(exp)
        logger.info(exp)
        print("--------------------------------------------------------------------------------")

        msg = "\n\n{} return tables have incorrect totals where activities have been recorded before stock (still counted) when ordered by activity date".format(len(incorrect_totals_out_of_order))
        print(msg)
        logger.info(msg)
        print(incorrect_totals_out_of_order)
        logger.info(incorrect_totals_out_of_order)
        exp = "\nThe total may still be correct when the activity date is disregarded or corrected. This report counts activities with dates recorded prior to stock (where all activities should be after stock)."
        print(exp)
        logger.info(exp)
        print("--------------------------------------------------------------------------------")

        msg = "\n\n{} return tables have incorrect totals with multiple stock rows when ordered by activity date".format(len(incorrect_totals_with_multiple_stocks))
        print(msg)
        logger.info(msg)
        print(incorrect_totals_with_multiple_stocks)
        logger.info(incorrect_totals_with_multiple_stocks)
        exp = "\nThe total may still be correct when the activity date is disregarded or corrected, as well as if the extra stock rows were to be corrected or counted as any other row."
        print(exp)
        logger.info(exp)
        print("--------------------------------------------------------------------------------")

        msg = "\n\n{} return tables have incorrect totals when ordered by date added, but correct when ordered by activity date".format(len(incorrect_totals_without_ordering_correct_with_ordering))
        print(msg)
        logger.info(msg)
        print(incorrect_totals_without_ordering_correct_with_ordering)
        logger.info(incorrect_totals_without_ordering_correct_with_ordering)
        exp = "\nThe totals for these return tables are correct when ordered by reported activity date but incorrect when ordered by when added. Can be left as is, may have even been remedied."
        print(exp)
        logger.info(exp)
        print("--------------------------------------------------------------------------------")

        msg = "\n\n{} return tables have rows with incorrect date of activity values/formats".format(len(bad_date_format))
        print(msg)
        logger.info(msg)
        print(bad_date_format)
        logger.info(bad_date_format)
        exp = "\nA bad date renders the return table unorderable. No further information will be available until this is remedied."
        print(exp)
        logger.info(exp)
        print("--------------------------------------------------------------------------------")

        msg = "\n\n{} return tables have incorrect totals when ordered by activity date".format(len(incorrect_totals))
        print(msg)
        logger.info(msg)
        print(incorrect_totals)
        logger.info(incorrect_totals)
        exp = "\nThe total may still be correct when the activity date is disregarded or corrected. But this error at least means that the activity dates provided do not match what should be expected."
        print(exp)
        logger.info(exp)
        print("--------------------------------------------------------------------------------")

        msg = "\n\n{} return tables have incorrect totals when ordered as added".format(len(incorrect_totals_regardless_ordering))
        print(msg)
        logger.info(msg)
        print(incorrect_totals_regardless_ordering)
        logger.info(incorrect_totals_regardless_ordering)
        exp = "\nThe totals for these return tables are incorrect even when disregarding multiple stock rows and incorrect activity date orders. These rows are ordered by whenever they had been added."
        print(exp)
        logger.info(exp)

