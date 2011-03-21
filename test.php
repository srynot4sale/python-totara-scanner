<?php

# Should find:
#
# 15 calls
# 7 faults (9, 21, 41, 63, 79, 85, 117)

# Bad cos never checked
$unchecked_result = get_records('users');

# OK, checked later
$checked_result = get_record_select('course');

# Returned so ignore (too hard to test correctly)
function returned_result() {
    return get_record('nah');
}

# Bad, returned before use (should be OK, too hard to test correctly)
function return_result() {
    $returned = get_record();
    return $returned;
}

# OK, result never used
function abandonded_result() {
    $abandon = get_record_sql('sql stuff');
}

# OK, checked
function simple_checked_result() {
    $checked = get_record();
    if (!$checked) {
        return false;
    }
    return true;
}

# Bad, used not checked
function use_raw_result() {
    $raw = get_records();
    foreach ($raw as $item) {
        echo $item;
    }
}

# OK, checked
function check_obj_result() {
    $result = new object();
    $result->item = get_record();

    if ($result->item) {
        return $result->item;
    }
    else {
        return false;
    }
}

# Bad, checking different property
function check_wrong_obj_result() {
    $result = new object();
    $result->thing = get_record();
    $result->status = 1;

    if ($result->status) {
        return $result->thing;
    }
}

# OK, check in if
function check_result() {
    $check = get_records();
    if (!$check) {
        return false;
    }

    # Bad, not tested
    $check = get_records();
    help($check);
}

# Bad, not checked but in if
function almost_checked_result() {
    $almost = get_records();
    if ($help) {
        strlen($almost);
    }
}

# OK, check in if
function check_immediately() {
    if (!$framework = get_record()) {
        return false;
    }
}

# OK, checked in teriary
function tertiary_result() {
    $ter = get_records();
    $result = $ter ? $ter : false;
}


class test {
    # good, checked
    function goodmethod() {
        $result = get_records();
        if (!$result) {
            return;
        }
        return $result;
    }

    # bad, not checked
    function badmethod() {
        $result = get_records();
        excellent($result);
    }
}


if (!$checked_result) {
    return false;
}
