#coding: utf-8
# Copyright 2016 Deep Datta
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
#  ofx.IifParser - Parsing Quickbook IIF.
#

from pyparsing import *
from collections import ChainMap

from fixofx.ofxtools import _ofxtoolsStartDebugAction, _ofxtoolsSuccessDebugAction, _ofxtoolsExceptionDebugAction

def _WT(token):    #Modify pyparsing tokens to keep whitespace and tabs intact
    token.parseWithTabs()
    token.leaveWhitespace()
    return token

def mk_dict_fn(tag):
    return (lambda t : {tag : t.asList()})

def dropQuotes(t):
    tok = t[0]
    if isinstance(tok, str):
        if (tok[0]=='"' and tok[-1]=='"') or (tok[0]=="'" and tok[-1]=="'"):
            return tok[1:-1]

class IifParser:
    trns_items = {
        "TRNSID"    : "Number",
        "TIMESTAMP" : "Timestamp",
        "TRNSTYPE"  : "Type",
        "DATE"	    : "Date",
        "ACCNT"	    : "Accnt",
        "NAME"	    : "Payee",
        "CLASS"	    : "Category",
        "AMOUNT"    : "Amount",
        "DOCNUM"    : "Docnum",
        "MEMO"	    : "Memo",
        "CLEAR"	    : "Clear",
        "PRICE"     : "Price"}

    spl_items = {
        "SPLID"     : "Splid",
        "TRNSTYPE"  : "Trnstype",
        "DATE"      : "Date",
        "ACCNT"     : "Accnt",
        "NAME"      : "Name",
        "CLASS"     : "Class",
        "AMOUNT"    : "Amount",
        "DOCNUM"    : "Docnum",
        "MEMO"      : "Memo",
        "CLEAR"     : "Clear",
        "PRICE"     : "Price",
        "QNTY"      : "Qnty",
        "INVITEM"   : "Invitem",
        "PAYMETH"   : "Paymeth",
        "TAXABLE"   : "Taxable",
        "REIMBEREXP": "Reimberexp",
        "EXTRA"     : "Extra",
        "VALDAJ"    : "Valdaj"}

    def __init__(self, debug=False):

        sep = Suppress('\t')
        eol = Suppress(ZeroOrMore(White(" \t")) + LineEnd())
        item = Regex("[^\t\r\n]*").setParseAction(dropQuotes)
        merge_dict_fn = lambda t: dict(ChainMap(*t))

        # Parse TRNS records
        trns_fields = delimitedList(oneOf(list(IifParser.trns_items)), sep).setParseAction(mk_dict_fn("TRNS_FLDS"))
        spl_fields  = delimitedList(oneOf(list(IifParser.spl_items)), sep).setParseAction(mk_dict_fn("SPL_FLDS"))
        trns_header = Suppress("!TRNS") + sep + trns_fields + eol +\
                      Suppress("!SPL") + sep + spl_fields + eol +\
                      Suppress("!ENDTRNS") + eol

        spl_entry = Suppress("SPL") + sep + Group(delimitedList(item, sep)) + eol
        trns_entry = Suppress("TRNS") + sep + delimitedList(item, sep).setParseAction(mk_dict_fn("TRN")) + eol +\
                     OneOrMore(spl_entry).setParseAction(mk_dict_fn("SPL")) + \
                     Suppress("ENDTRNS") + eol
        trns_entry.setParseAction(merge_dict_fn)

        trns_entries = (trns_header + ZeroOrMore(trns_entry).setParseAction(mk_dict_fn("TRNS"))).setParseAction(merge_dict_fn)
        transactions = Group(trns_entries)("TRANSACTS*")

        self.parser = transactions


        self.parser.leaveWhitespace()
        self.parser.parseWithTabs()

        if (debug):
            self.parser.setDebugActions(_ofxtoolsStartDebugAction,
                                        _ofxtoolsSuccessDebugAction,
                                        _ofxtoolsExceptionDebugAction)

    def parse(self, iif):
        return self.parser.parseString(iif)

    @classmethod
    def get_txn_list(cls, trns_block):
        txn_list = []
        trns_fields = trns_block["TRNS_FLDS"]
        trns = trns_block["TRNS"]
        if not len(trns):
            return txn_list

        for trn_rec in trns:
            trn = trn_rec["TRN"]
            txn = {}
            for i, fld in enumerate(trn):
                txn[IifParser.trns_items[trns_fields[i]]] = fld
            txn_list.append(txn)

        return txn_list


def _main():
    f = open(sys.argv[1], 'r', encoding="latin-1")
    """
    for line in f:
       print(":".join("{:02x}".format(ord(c)) for c in line))
       break
    return
    """
    
    text = f.read()
    iifp = IifParser(debug=0)
    p = iifp.parse(text)

    import json
    #print(json.dumps(p["TRANSACTS"].asList()))
    print((p["TRANSACTS"][0][0]))
    #p.dump()

if __name__ == "__main__":
    import sys
    _main()
