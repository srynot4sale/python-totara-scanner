<?php

# Should find:
#
# 12 calls
# 5 faults

# Bad cos never checked
$unchecked_result = get_records('users');

# OK, checked later
$checked_result = get_record_select('course');

# Returned so ignore (too hard to test correctly)
function returned_result() {
    return get_record('nah');
}

# OK, returned before use (too hard to test correctly)
function return_result() {
    $returned = get_record();
    return $returned;
}

# OK, result never used
function abandonded_result() {
    $abandon = get_record_sql('sql stuff');
}

# Bad, used not checked
function use_raw_result() {
    $raw = get_records();
    foreach ($raw as $item) {
        echo $item;
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
    if (1) {
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
        if ($result) {
            return;
        }
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