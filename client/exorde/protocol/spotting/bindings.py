import logging
from aiosow.bindings import setup, wire
from aiosow.perpetuate import on

from exorde.formated import on_formated_data_do

from typing import Callable
from exorde.protocol.ipfs.bindings import push_to_ipfs, on_new_cid_do
from exorde.protocol.base.bindings import commit_current_cid
from exorde.protocol.spotting import (
    init_stack,
    push_to_stack,
    consume_processed,
    reset_cids,
    push_new_cid,
    choose_cid_to_commit,
    pull_to_process,
)


SPOTTING_PROCCESES: list[Callable] = []


def spotting(function: Callable):
    SPOTTING_PROCCESES.append(function)
    return function


setup(init_stack)
setup(reset_cids)


spotting_ran_when, on_spotting_done_do = wire(perpetual=True)


@on_formated_data_do
@spotting_ran_when
async def run_spotting(item: dict):
    return item


# on_formated_data_do(push_to_stack)
on_spotting_done_do(push_to_stack)


on(
    "stack",
    condition=lambda stack, processing, running: len(stack) >= 1
    and not processing
    and running,
)(pull_to_process)
# on("stack")(call_limit(1)(log_stack_len))
on("processed", condition=lambda processed: len(processed) == 25)(
    consume_processed
)
on(
    "processed",
    lambda processed: logging.info("processed: %d", len(processed)),
)
on(
    "batch_to_consume",
    condition=lambda value, transaction, batch_id: value
    and not transaction
    and not batch_id,
)(push_to_ipfs)
on_new_cid_do(push_new_cid)
on("cids", condition=lambda cids: len(cids))(
    lambda __cids__: logging.info(f"A batch has been uploaded to IPFS")
)
on(
    "cids",
    condition=lambda cids, current_cid_commit: len(cids)
    and not current_cid_commit,
)(choose_cid_to_commit)
on_new_cid_to_commit = on("current_cid_commit", condition=lambda value: value)
on_new_cid_to_commit(
    lambda value: logging.info(
        f"New CID has been choosen for ritual transaction ({value})"
    )
)
on_new_cid_to_commit(commit_current_cid)
