# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# util __init__.py

from __future__ import unicode_literals
from werkzeug.test import Client
import os
import re
import urllib
import frappe
import datetime
import math

no_value_fields = ['Section Break', 'Column Break', 'HTML', 'Table', 'FlexTable',
	'Button', 'Image', 'Graph']
default_fields = ['doctype', 'name', 'owner', 'creation', 'modified', 'modified_by',
	'parent', 'parentfield', 'parenttype', 'idx', 'docstatus']

# used in import_docs.py
# TODO: deprecate it
def getCSVelement(v):
	"""
		 Returns the CSV value of `v`, For example:

		 * apple becomes "apple"
		 * hi"there becomes "hi""there"
	"""
	v = cstr(v)
	if not v: return ''
	if (',' in v) or ('\n' in v) or ('"' in v):
		if '"' in v: v = v.replace('"', '""')
		return '"'+v+'"'
	else: return v or ''

def get_fullname(user):
	"""get the full name (first name + last name) of the user from User"""
	if not hasattr(frappe.local, "fullnames"):
		frappe.local.fullnames = {}

	if not frappe.local.fullnames.get(user):
		p = frappe.db.get_value("User", user, ["first_name", "last_name"], as_dict=True)
		if p:
			frappe.local.fullnames[user] = " ".join(filter(None,
				[p.get('first_name'), p.get('last_name')])) or user
		else:
			frappe.local.fullnames[user] = user

	return frappe.local.fullnames.get(user)

def get_formatted_email(user):
	"""get email id of user formatted as: John Doe <johndoe@example.com>"""
	if user == "Administrator":
		return user
	from email.utils import formataddr
	fullname = get_fullname(user)
	return formataddr((fullname, user))

def extract_email_id(email):
	"""fetch only the email part of the email id"""
	from email.utils import parseaddr
	fullname, email_id = parseaddr(email)
	if isinstance(email_id, basestring) and not isinstance(email_id, unicode):
		email_id = email_id.decode("utf-8", "ignore")
	return email_id

def validate_email_add(email_str):
	"""Validates the email string"""
	email = extract_email_id(email_str)
	return re.match("[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", email.lower())

def random_string(length):
	"""generate a random string"""
	import string
	from random import choice
	return ''.join([choice(string.letters + string.digits) for i in range(length)])

def get_traceback():
	"""
		 Returns the traceback of the Exception
	"""
	import sys, traceback
	exc_type, value, tb = sys.exc_info()

	trace_list = traceback.format_tb(tb, None) + \
		traceback.format_exception_only(exc_type, value)
	body = "Traceback (innermost last):\n" + "%-20s %s" % \
		(unicode((b"").join(trace_list[:-1]), 'utf-8'), unicode(trace_list[-1], 'utf-8'))

	if frappe.logger:
		frappe.logger.error('Db:'+(frappe.db and frappe.db.cur_db_name or '') \
			+ ' - ' + body)

	return body

def log(event, details):
	frappe.logger.info(details)

# datetime functions
def getdate(string_date):
	"""
		 Coverts string date (yyyy-mm-dd) to datetime.date object
	"""
	if isinstance(string_date, datetime.date):
		return string_date
	elif isinstance(string_date, datetime.datetime):
		return datetime.date()

	if " " in string_date:
		string_date = string_date.split(" ")[0]

	return datetime.datetime.strptime(string_date, "%Y-%m-%d").date()

def add_to_date(date, years=0, months=0, days=0):
	"""Adds `days` to the given date"""
	format = isinstance(date, basestring)
	if date:
		date = getdate(date)
	else:
		raise Exception, "Start date required"

	from dateutil.relativedelta import relativedelta
	date += relativedelta(years=years, months=months, days=days)

	if format:
		return date.strftime("%Y-%m-%d")
	else:
		return date

def add_days(date, days):
	return add_to_date(date, days=days)

def add_months(date, months):
	return add_to_date(date, months=months)

def add_years(date, years):
	return add_to_date(date, years=years)

def date_diff(string_ed_date, string_st_date):
	return (getdate(string_ed_date) - getdate(string_st_date)).days

def time_diff(string_ed_date, string_st_date):
	return get_datetime(string_ed_date) - get_datetime(string_st_date)

def time_diff_in_seconds(string_ed_date, string_st_date):
	return time_diff(string_ed_date, string_st_date).seconds

def time_diff_in_hours(string_ed_date, string_st_date):
	return round(float(time_diff(string_ed_date, string_st_date).seconds) / 3600, 6)

def now_datetime():
	return convert_utc_to_user_timezone(datetime.datetime.utcnow())

def get_user_time_zone():
	if getattr(frappe.local, "user_time_zone", None) is None:
		frappe.local.user_time_zone = frappe.cache().get_value("time_zone")

	if not frappe.local.user_time_zone:
		frappe.local.user_time_zone = frappe.db.get_default('time_zone') or 'Asia/Calcutta'
		frappe.cache().set_value("time_zone", frappe.local.user_time_zone)

	return frappe.local.user_time_zone

def convert_utc_to_user_timezone(utc_timestamp):
	from pytz import timezone, UnknownTimeZoneError
	utcnow = timezone('UTC').localize(utc_timestamp)
	try:
		return utcnow.astimezone(timezone(get_user_time_zone()))
	except UnknownTimeZoneError:
		return utcnow

def now():
	"""return current datetime as yyyy-mm-dd hh:mm:ss"""
	if getattr(frappe.local, "current_date", None):
		return getdate(frappe.local.current_date).strftime("%Y-%m-%d") + " " + \
			now_datetime().strftime('%H:%M:%S.%f')
	else:
		return now_datetime().strftime('%Y-%m-%d %H:%M:%S.%f')

def nowdate():
	"""return current date as yyyy-mm-dd"""
	return now_datetime().strftime('%Y-%m-%d')

def today():
	return nowdate()

def nowtime():
	"""return current time in hh:mm"""
	return now_datetime().strftime('%H:%M:%S.%f')

def get_first_day(dt, d_years=0, d_months=0):
	"""
	 Returns the first day of the month for the date specified by date object
	 Also adds `d_years` and `d_months` if specified
	"""
	dt = getdate(dt)

	# d_years, d_months are "deltas" to apply to dt
	overflow_years, month = divmod(dt.month + d_months - 1, 12)
	year = dt.year + d_years + overflow_years

	return datetime.date(year, month + 1, 1)

def get_last_day(dt):
	"""
	 Returns last day of the month using:
	 `get_first_day(dt, 0, 1) + datetime.timedelta(-1)`
	"""
	return get_first_day(dt, 0, 1) + datetime.timedelta(-1)

def get_datetime(datetime_str):
	try:
		return datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')

	except TypeError:
		if isinstance(datetime_str, datetime.datetime):
			return datetime_str.replace(tzinfo=None)
		else:
			raise

	except ValueError:
		if datetime_str=='0000-00-00 00:00:00.000000':
			return None

		return datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

def get_datetime_str(datetime_obj):
	if isinstance(datetime_obj, basestring):
		datetime_obj = get_datetime(datetime_obj)

	return datetime_obj.strftime('%Y-%m-%d %H:%M:%S.%f')

def formatdate(string_date=None):
	"""
	 	Convers the given string date to :data:`user_format`
		User format specified in defaults

		 Examples:

		 * dd-mm-yyyy
		 * mm-dd-yyyy
		 * dd/mm/yyyy
	"""
	if string_date:
		string_date = getdate(string_date)
	else:
		string_date = now_datetime().date()

	if getattr(frappe.local, "user_format", None) is None:
		frappe.local.user_format = frappe.db.get_default("date_format")

	out = frappe.local.user_format

	return out.replace("dd", string_date.strftime("%d"))\
		.replace("mm", string_date.strftime("%m"))\
		.replace("yyyy", string_date.strftime("%Y"))

def global_date_format(date):
	"""returns date as 1 January 2012"""
	formatted_date = getdate(date).strftime("%d %B %Y")
	return formatted_date.startswith("0") and formatted_date[1:] or formatted_date

def dict_to_str(args, sep='&'):
	"""
	Converts a dictionary to URL
	"""
	t = []
	for k in args.keys():
		t.append(str(k)+'='+urllib.quote(str(args[k] or '')))
	return sep.join(t)

def has_common(l1, l2):
	"""Returns truthy value if there are common elements in lists l1 and l2"""
	return set(l1) & set(l2)

def flt(s, precision=None):
	"""Convert to float (ignore commas)"""
	if isinstance(s, basestring):
		s = s.replace(',','')
	try:
		num = float(s)
		if precision is not None:
			num = _round(num, precision)
	except Exception:
		num = 0
	return num

def cint(s):
	"""Convert to integer"""
	try: num = int(float(s))
	except: num = 0
	return num

def cstr(s):
	if isinstance(s, unicode):
		return s
	elif s==None:
		return ''
	elif isinstance(s, basestring):
		return unicode(s, 'utf-8')
	else:
		return unicode(s)

def _round(num, precision=0):
	"""round method for round halfs to nearest even algorithm"""
	precision = cint(precision)
	multiplier = 10 ** precision

	# avoid rounding errors
	num = round(num * multiplier if precision else num, 8)

	floor = math.floor(num)
	decimal_part = num - floor

	if decimal_part == 0.5:
		num = floor if (floor % 2 == 0) else floor + 1
	else:
		num = round(num)

	return (num / multiplier) if precision else num

def encode(obj, encoding="utf-8"):
	if isinstance(obj, list):
		out = []
		for o in obj:
			if isinstance(o, unicode):
				out.append(o.encode(encoding))
			else:
				out.append(o)
		return out
	elif isinstance(obj, unicode):
		return obj.encode(encoding)
	else:
		return obj

def parse_val(v):
	"""Converts to simple datatypes from SQL query results"""
	if isinstance(v, (datetime.date, datetime.datetime)):
		v = unicode(v)
	elif isinstance(v, datetime.timedelta):
		v = ":".join(unicode(v).split(":")[:2])
	elif isinstance(v, long):
		v = int(v)
	return v

def fmt_money(amount, precision=None, currency=None):
	"""
	Convert to string with commas for thousands, millions etc
	"""
	number_format = frappe.db.get_default("number_format") or "#,###.##"
	decimal_str, comma_str, precision = get_number_format_info(number_format)


	amount = '%.*f' % (precision, flt(amount))
	if amount.find('.') == -1:
		decimals = ''
	else:
		decimals = amount.split('.')[1]

	parts = []
	minus = ''
	if flt(amount) < 0:
		minus = '-'

	amount = cstr(abs(flt(amount))).split('.')[0]

	if len(amount) > 3:
		parts.append(amount[-3:])
		amount = amount[:-3]

		val = number_format=="#,##,###.##" and 2 or 3

		while len(amount) > val:
			parts.append(amount[-val:])
			amount = amount[:-val]

	parts.append(amount)

	parts.reverse()

	amount = comma_str.join(parts) + (precision and (decimal_str + decimals) or "")
	amount = minus + amount

	if currency:
		symbol = frappe.db.get_value("Currency", currency, "symbol")
		if symbol:
			amount = symbol + " " + amount

	return amount

number_format_info = {
	"#.###": ("", ".", 0),
	"#,###": ("", ",", 0),
	"#,###.##": (".", ",", 2),
	"#,##,###.##": (".", ",", 2),
	"#.###,##": (",", ".", 2),
	"# ###.##": (".", " ", 2),
	"#,###.###": (".", ",", 3),
}

def get_number_format_info(format):
	return number_format_info.get(format) or (".", ",", 2)

#
# convet currency to words
#
def money_in_words(number, main_currency = None, fraction_currency=None):
	"""
	Returns string in words with currency and fraction currency.
	"""

	d = get_defaults()
	if not main_currency:
		main_currency = d.get('currency', 'INR')
	if not fraction_currency:
		fraction_currency = frappe.db.get_value("Currency", main_currency, "fraction") or "Cent"

	n = "%.2f" % flt(number)
	main, fraction = n.split('.')
	if len(fraction)==1: fraction += '0'


	number_format = frappe.db.get_value("Currency", main_currency, "number_format") or \
		frappe.db.get_default("number_format") or "#,###.##"

	in_million = True
	if number_format == "#,##,###.##": in_million = False

	out = main_currency + ' ' + in_words(main, in_million).title()
	if cint(fraction):
		out = out + ' and ' + in_words(fraction, in_million).title() + ' ' + fraction_currency

	return out + ' only.'

#
# convert number to words
#
def in_words(integer, in_million=True):
	"""
	Returns string in words for the given integer.
	"""
	n=int(integer)
	known = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten',
		11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen', 15: 'fifteen', 16: 'sixteen', 17: 'seventeen', 18: 'eighteen',
		19: 'nineteen', 20: 'twenty', 30: 'thirty', 40: 'forty', 50: 'fifty', 60: 'sixty', 70: 'seventy', 80: 'eighty', 90: 'ninety'}

	def psn(n, known, xpsn):
		import sys;
		if n in known: return known[n]
		bestguess, remainder = str(n), 0

		if n<=20:
			frappe.errprint(sys.stderr)
			frappe.errprint(n)
			frappe.errprint("How did this happen?")
			assert 0
		elif n < 100:
			bestguess= xpsn((n//10)*10, known, xpsn) + '-' + xpsn(n%10, known, xpsn)
			return bestguess
		elif n < 1000:
			bestguess= xpsn(n//100, known, xpsn) + ' ' + 'hundred'
			remainder = n%100
		else:
			if in_million:
				if n < 1000000:
					bestguess= xpsn(n//1000, known, xpsn) + ' ' + 'thousand'
					remainder = n%1000
				elif n < 1000000000:
					bestguess= xpsn(n//1000000, known, xpsn) + ' ' + 'million'
					remainder = n%1000000
				else:
					bestguess= xpsn(n//1000000000, known, xpsn) + ' ' + 'billion'
					remainder = n%1000000000
			else:
				if n < 100000:
					bestguess= xpsn(n//1000, known, xpsn) + ' ' + 'thousand'
					remainder = n%1000
				elif n < 10000000:
					bestguess= xpsn(n//100000, known, xpsn) + ' ' + 'lakh'
					remainder = n%100000
				else:
					bestguess= xpsn(n//10000000, known, xpsn) + ' ' + 'crore'
					remainder = n%10000000
		if remainder:
			if remainder >= 100:
				comma = ','
			else:
				comma = ''
			return bestguess + comma + ' ' + xpsn(remainder, known, xpsn)
		else:
			return bestguess

	return psn(n, known, psn)

# Get Defaults
# ==============================================================================

def get_defaults(key=None):
	"""
	Get dictionary of default values from the defaults, or a value if key is passed
	"""
	return frappe.db.get_defaults(key)

def set_default(key, val):
	"""
	Set / add a default value to defaults`
	"""
	return frappe.db.set_default(key, val)

def remove_blanks(d):
	"""
		Returns d with empty ('' or None) values stripped
	"""
	empty_keys = []
	for key in d:
		if d[key]=='' or d[key]==None:
			# del d[key] raises runtime exception, using a workaround
			empty_keys.append(key)
	for key in empty_keys:
		del d[key]

	return d

def pprint_dict(d, level=1, no_blanks=True):
	"""
		Pretty print a dictionary with indents
	"""
	if no_blanks:
		remove_blanks(d)

	# make indent
	indent, ret = '', ''
	for i in range(0,level): indent += '\t'

	# add lines
	comment, lines = '', []
	kl = d.keys()
	kl.sort()

	# make lines
	for key in kl:
		if key != '##comment':
			tmp = {key: d[key]}
			lines.append(indent + str(tmp)[1:-1] )

	# add comment string
	if '##comment' in kl:
		ret = ('\n' + indent) + '# ' + d['##comment'] + '\n'

	# open
	ret += indent + '{\n'

	# lines
	ret += indent + ',\n\t'.join(lines)

	# close
	ret += '\n' + indent + '}'

	return ret

def get_common(d1,d2):
	"""
		returns (list of keys) the common part of two dicts
	"""
	return [p for p in d1 if p in d2 and d1[p]==d2[p]]

def get_common_dict(d1, d2):
	"""
		return common dictionary of d1 and d2
	"""
	ret = {}
	for key in d1:
		if key in d2 and d2[key]==d1[key]:
			ret[key] = d1[key]
	return ret

def get_diff_dict(d1, d2):
	"""
		return common dictionary of d1 and d2
	"""
	diff_keys = set(d2.keys()).difference(set(d1.keys()))

	ret = {}
	for d in diff_keys: ret[d] = d2[d]
	return ret


def get_file_timestamp(fn):
	"""
		Returns timestamp of the given file
	"""
	from frappe.utils import cint

	try:
		return str(cint(os.stat(fn).st_mtime))
	except OSError, e:
		if e.args[0]!=2:
			raise
		else:
			return None

# to be deprecated
def make_esc(esc_chars):
	"""
		Function generator for Escaping special characters
	"""
	return lambda s: ''.join(['\\' + c if c in esc_chars else c for c in s])

# esc / unescape characters -- used for command line
def esc(s, esc_chars):
	"""
		Escape special characters
	"""
	if not s:
		return ""
	for c in esc_chars:
		esc_str = '\\' + c
		s = s.replace(c, esc_str)
	return s

def unesc(s, esc_chars):
	"""
		UnEscape special characters
	"""
	for c in esc_chars:
		esc_str = '\\' + c
		s = s.replace(esc_str, c)
	return s

def is_html(text):
	out = False
	for key in ["<br>", "<p", "<img", "<div"]:
		if key in text:
			out = True
			break
	return out

def strip_html(text):
	"""
		removes anything enclosed in and including <>
	"""
	return re.compile(r'<.*?>').sub('', text)

def escape_html(text):
	html_escape_table = {
		"&": "&amp;",
		'"': "&quot;",
		"'": "&apos;",
		">": "&gt;",
		"<": "&lt;",
	}

	return "".join(html_escape_table.get(c,c) for c in text)

def get_doctype_label(dt=None):
	"""
		Gets label of a doctype
	"""
	if dt:
		res = frappe.db.sql("""\
			SELECT name, dt_label FROM `tabDocType Label`
			WHERE name=%s""", dt)
		return res and res[0][0] or dt
	else:
		res = frappe.db.sql("SELECT name, dt_label FROM `tabDocType Label`")
		dt_label_dict = {}
		for r in res:
			dt_label_dict[r[0]] = r[1]

		return dt_label_dict


def get_label_doctype(label):
	"""
		Gets doctype from its label
	"""
	res = frappe.db.sql("""\
		SELECT name FROM `tabDocType Label`
		WHERE dt_label=%s""", label)

	return res and res[0][0] or label


def pretty_date(iso_datetime):
	"""
		Takes an ISO time and returns a string representing how
		long ago the date represents.
		Ported from PrettyDate by John Resig
	"""
	if not iso_datetime: return ''
	import math

	if isinstance(iso_datetime, basestring):
		iso_datetime = datetime.datetime.strptime(iso_datetime, '%Y-%m-%d %H:%M:%S.%f')
	now_dt = datetime.datetime.strptime(now(), '%Y-%m-%d %H:%M:%S.%f')
	dt_diff = now_dt - iso_datetime

	# available only in python 2.7+
	# dt_diff_seconds = dt_diff.total_seconds()

	dt_diff_seconds = dt_diff.days * 86400.0 + dt_diff.seconds

	dt_diff_days = math.floor(dt_diff_seconds / 86400.0)

	# differnt cases
	if dt_diff_seconds < 60.0:
		return 'just now'
	elif dt_diff_seconds < 120.0:
		return '1 minute ago'
	elif dt_diff_seconds < 3600.0:
		return '%s minutes ago' % cint(math.floor(dt_diff_seconds / 60.0))
	elif dt_diff_seconds < 7200.0:
		return '1 hour ago'
	elif dt_diff_seconds < 86400.0:
		return '%s hours ago' % cint(math.floor(dt_diff_seconds / 3600.0))
	elif dt_diff_days == 1.0:
		return 'Yesterday'
	elif dt_diff_days < 7.0:
		return '%s days ago' % cint(dt_diff_days)
	elif dt_diff_days < 31.0:
		return '%s week(s) ago' % cint(math.ceil(dt_diff_days / 7.0))
	elif dt_diff_days < 365.0:
		return '%s months ago' % cint(math.ceil(dt_diff_days / 30.0))
	else:
		return 'more than %s year(s) ago' % cint(math.floor(dt_diff_days / 365.0))

def execute_in_shell(cmd, verbose=0):
	# using Popen instead of os.system - as recommended by python docs
	from subprocess import Popen
	import tempfile

	with tempfile.TemporaryFile() as stdout:
		with tempfile.TemporaryFile() as stderr:
			p = Popen(cmd, shell=True, stdout=stdout, stderr=stderr)
			p.wait()

			stdout.seek(0)
			out = stdout.read()

			stderr.seek(0)
			err = stderr.read()

	if verbose:
		if err: print err
		if out: print out

	return err, out

def comma_or(some_list):
	return comma_sep(some_list, " or ")

def comma_and(some_list):
	return comma_sep(some_list, " and ")

def comma_sep(some_list, sep):
	if isinstance(some_list, (list, tuple)):
		# list(some_list) is done to preserve the existing list
		some_list = [unicode(s) for s in list(some_list)]
		if not some_list:
			return ""
		elif len(some_list) == 1:
			return some_list[0]
		else:
			some_list = ["'%s'" % s for s in some_list]
			return ", ".join(some_list[:-1]) + sep + some_list[-1]
	else:
		return some_list

def filter_strip_join(some_list, sep):
	"""given a list, filter None values, strip spaces and join"""
	return (cstr(sep)).join((cstr(a).strip() for a in filter(None, some_list)))

def get_path(*path, **kwargs):
	base = kwargs.get('base')
	if not base:
		base = frappe.local.site_path
	return os.path.join(base, *path)

def get_site_base_path(sites_dir=None, hostname=None):
	return frappe.local.site_path

def get_site_path(*path):
	return get_path(base=get_site_base_path(), *path)

def get_files_path(*path):
	return get_site_path("public", "files", *path)

def get_backups_path():
	return get_site_path("private", "backups")

def get_request_site_address(full_address=False):
	return get_url(full_address=full_address)

def get_url(uri=None, full_address=False):
	"""get app url from request"""
	host_name = frappe.local.conf.host_name

	if not host_name:
		if hasattr(frappe.local, "request") and frappe.local.request and frappe.local.request.host:
			protocol = 'https' == frappe.get_request_header('X-Forwarded-Proto', "") and 'https://' or 'http://'
			host_name = protocol + frappe.local.request.host
		elif frappe.local.site:
			host_name = "http://{}".format(frappe.local.site)
		else:
			host_name = frappe.db.get_value("Website Settings", "Website Settings",
				"subdomain")
			if host_name and "http" not in host_name:
				host_name = "http://" + host_name

			if not host_name:
				host_name = "http://localhost"

	if not uri and full_address:
		uri = frappe.get_request_header("REQUEST_URI", "")

	url = urllib.basejoin(host_name, uri) if uri else host_name

	return url

def get_url_to_form(doctype, name, base_url=None, label=None):
	if not base_url:
		base_url = get_url()

	if not label: label = name

	return """<a href="%(base_url)s/desk#!Form/%(doctype)s/%(name)s">%(label)s</a>""" % locals()

def encode_dict(d, encoding="utf-8"):
	for key in d:
		if isinstance(d[key], basestring) and isinstance(d[key], unicode):
			d[key] = d[key].encode(encoding)

	return d

def decode_dict(d, encoding="utf-8"):
	for key in d:
		if isinstance(d[key], basestring) and not isinstance(d[key], unicode):
			d[key] = d[key].decode(encoding, "ignore")

	return d


import operator
operator_map = {
	# startswith
	"^": lambda (a, b): (a or "").startswith(b),

	# in or not in a list
	"in": lambda (a, b): operator.contains(b, a),
	"not in": lambda (a, b): not operator.contains(b, a),

	# comparison operators
	"=": lambda (a, b): operator.eq(a, b),
	"!=": lambda (a, b): operator.ne(a, b),
	">": lambda (a, b): operator.gt(a, b),
	"<": lambda (a, b): operator.lt(a, b),
	">=": lambda (a, b): operator.ge(a, b),
	"<=": lambda (a, b): operator.le(a, b),
	"not None": lambda (a, b): a and True or False,
	"None": lambda (a, b): (not a) and True or False
}

def compare(val1, condition, val2):
	ret = False
	if condition in operator_map:
		ret = operator_map[condition]((val1, val2))

	return ret

def get_site_name(hostname):
	return hostname.split(':')[0]

def get_disk_usage():
	"""get disk usage of files folder"""
	files_path = get_files_path()
	if not os.path.exists(files_path):
		return 0
	err, out = execute_in_shell("du -hsm {files_path}".format(files_path=files_path))
	return cint(out.split("\n")[-2].split("\t")[0])

def scrub_urls(html):
	html = expand_relative_urls(html)
	html = quote_urls(html)
	return html

def expand_relative_urls(html):
	# expand relative urls
	url = get_url()
	if url.endswith("/"): url = url[:-1]

	def _expand_relative_urls(match):
		to_expand = list(match.groups())
		if not to_expand[2].startswith("/"):
			to_expand[2] = "/" + to_expand[2]
		to_expand.insert(2, url)
		return "".join(to_expand)

	return re.sub('(href|src){1}([\s]*=[\s]*[\'"]?)((?!http)[^\'" >]+)([\'"]?)', _expand_relative_urls, html)

def quote_urls(html):
	def _quote_url(match):
		groups = list(match.groups())
		groups[2] = urllib.quote(groups[2], safe="~@#$&()*!+=:;,.?/'")
		return "".join(groups)
	return re.sub('(href|src){1}([\s]*=[\s]*[\'"]?)((?:http)[^\'">]+)([\'"]?)',
		_quote_url, html)

def touch_file(path):
	with open(path, 'a'):
		os.utime(path, None)
	return True

def get_test_client():
	from frappe.app import application
	return Client(application)

def get_hook_method(hook_name, fallback=None):
	method = (frappe.get_hooks().get(hook_name))
	if method:
		method = frappe.get_attr(method[0])
		return method
	if fallback:
		return fallback
