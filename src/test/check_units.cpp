// Checks the unit metadata on every openocean message:
//
//  1. Every numeric (non-enum, non-bool) field declares its units, either
//     statically with (openocean.field).units or at runtime with
//     (openocean.field).units_field naming a sibling string field.
//  2. Every static units string parses with UDUNITS-2.
//  3. ControlSetpoint stays aligned with Navigation: a field that shares a name
//     with a Navigation field must also share its number and units.
//
// Prints one line per problem and exits non-zero if there were any.

#include <iostream>
#include <string>
#include <vector>

#include <udunits2.h>

#include "messages/control.pb.h"
#include "messages/navigation.pb.h"
#include "messages/options.pb.h"

using google::protobuf::Descriptor;
using google::protobuf::FieldDescriptor;

namespace
{
int errors = 0;

void fail(const FieldDescriptor* field, const std::string& why)
{
    std::cerr << field->full_name() << ": " << why << "\n";
    ++errors;
}

bool is_numeric(const FieldDescriptor* field)
{
    switch (field->cpp_type())
    {
        case FieldDescriptor::CPPTYPE_INT32:
        case FieldDescriptor::CPPTYPE_INT64:
        case FieldDescriptor::CPPTYPE_UINT32:
        case FieldDescriptor::CPPTYPE_UINT64:
        case FieldDescriptor::CPPTYPE_DOUBLE:
        case FieldDescriptor::CPPTYPE_FLOAT: return true;
        default: return false;
    }
}

void check_message(const Descriptor* desc, ut_system* units_system)
{
    for (int i = 0; i < desc->field_count(); ++i)
    {
        const FieldDescriptor* field = desc->field(i);
        const auto& opts = field->options().GetExtension(openocean::field);

        if (!opts.units().empty() && !opts.units_field().empty())
            fail(field, "sets both units and units_field");

        if (!opts.units().empty())
        {
            ut_unit* unit = ut_parse(units_system, opts.units().c_str(), UT_UTF8);
            if (!unit)
                fail(field, "UDUNITS-2 cannot parse \"" + opts.units() + "\"");
            ut_free(unit);
        }
        else if (!opts.units_field().empty())
        {
            const FieldDescriptor* sibling = desc->FindFieldByName(opts.units_field());
            if (!sibling || sibling->cpp_type() != FieldDescriptor::CPPTYPE_STRING)
                fail(field, "units_field \"" + opts.units_field() +
                                "\" is not a string field of " + desc->name());
        }
        else if (is_numeric(field))
        {
            fail(field, "numeric field has no units");
        }

        if (field->message_type())
            check_message(field->message_type(), units_system);
    }
}

void check_aligned(const Descriptor* desc, const Descriptor* reference)
{
    for (int i = 0; i < desc->field_count(); ++i)
    {
        const FieldDescriptor* field = desc->field(i);
        const FieldDescriptor* ref = reference->FindFieldByName(field->name());
        if (!ref)
            continue;
        if (field->number() != ref->number())
            fail(field, "number " + std::to_string(field->number()) + " differs from " +
                            ref->full_name() + " (" + std::to_string(ref->number()) + ")");
        const auto& units = field->options().GetExtension(openocean::field).units();
        const auto& ref_units = ref->options().GetExtension(openocean::field).units();
        if (units != ref_units)
            fail(field, "units \"" + units + "\" differ from " + ref->full_name() + " (\"" +
                            ref_units + "\")");
    }
}
} // namespace

int main()
{
    ut_set_error_message_handler(ut_ignore);
    ut_system* units_system = ut_read_xml(nullptr);
    if (!units_system)
    {
        std::cerr << "Cannot read the UDUNITS-2 unit database\n";
        return 1;
    }

    const std::vector<const Descriptor*> messages = {openocean::Navigation::descriptor(),
                                                     openocean::ControlSetpoint::descriptor()};
    for (const Descriptor* desc : messages) check_message(desc, units_system);

    check_aligned(openocean::ControlSetpoint::descriptor(), openocean::Navigation::descriptor());

    ut_free_system(units_system);

    if (errors == 0)
        std::cout << "All units valid and ControlSetpoint aligned with Navigation\n";
    return errors == 0 ? 0 : 1;
}
