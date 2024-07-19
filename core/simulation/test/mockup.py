
from typing import Self
from unittest import TestCase
from core.data.data_provider import (ChunkIterator, ChunkProvider, ChunkReader,
                                     ChunkType, ContinuousProvider, Sample)


class DummyContProvider(ContinuousProvider):
    def __init__(self, ut: TestCase) -> None:
        self.test = ut

        self.last_iter_type = None
        self.expected_update_sample = None

        self.next_sample = None

    def _pop(self):
        if isinstance(self.next_sample, list):
            ns = self.next_sample[0]
            if len(self.next_sample) > 1:
                self.next_sample = self.next_sample[1:]
            else:
                self.next_sample = self.next_sample[0]
        else:
            ns = self.next_sample
        return Sample(ns.tensor, ns.context.copy())

    def get_iterator(self, chunk_type: ChunkType) -> Self:
        self.last_iter_type = chunk_type
        return self

    def __next__(self) -> Sample:
        return self._pop()

    def update_sample(self, sample: Sample) -> None:
        self.test.assertEqual(self.expected_update_sample, sample)
        return self._pop()


class DummyChunkReader(ChunkReader):
    def __init__(self, ut: TestCase, parent: "DummyChunkProvider") -> None:
        self.test = ut
        self.parent = parent

    def _pop(self):
        if isinstance(self.parent.next_sample, list):
            ns = self.parent.next_sample[0]
            if len(self.parent.next_sample) > 1:
                self.parent.next_sample = self.parent.next_sample[1:]
            else:
                self.parent.next_sample = self.parent.next_sample[0]
        else:
            ns = self.parent.next_sample
        return Sample(ns.tensor, ns.context.copy())

    def __next__(self) -> Sample:
        if self.is_exhausted():
            raise StopIteration()
        return self._pop()

    def __len__(self) -> int:
        return 0

    def is_exhausted(self) -> bool:
        return self.parent.reader_exhausted


class DummyIter(ChunkIterator):
    def __init__(self, ut: TestCase, parent: "DummyChunkProvider") -> None:
        self.test = ut
        self.parent = parent

    def __next__(self) -> ChunkReader:
        if self.parent.last_chunk_reached:
            raise StopIteration

        self.parent.next_was_called = True
        self.parent.reader_exhausted = False

        return DummyChunkReader(self.test, self.parent)

    def __len__(self) -> int:
        return 0


class DummyChunkProvider(ChunkProvider):
    def __init__(self, ut: TestCase) -> None:
        self.test = ut

        self.last_iter_type = None

        self.next_sample = None
        self.chunk_signature = None
        self.last_chunk_reached = False
        self.reader_exhausted = False
        self.next_was_called = False

    def assert_chunk_change(self):
        self.test.assertTrue(self.next_was_called)
        self.next_was_called = False

    def assert_no_chunk_change(self):
        self.test.assertFalse(self.next_was_called)

    def get_iterator(self, chunk_type: ChunkType):
        self.last_iter_type = chunk_type
        return DummyIter(self.test, self)

    def get_chunk_signature(self) -> str:
        return self.chunk_signature

