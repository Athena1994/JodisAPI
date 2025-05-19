
from dataclasses import dataclass


@dataclass
class Version:
    """
    Class representing the version of the system.
    """

    major: int
    minor: int
    patch: int

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    @staticmethod
    def parse(version_str: str) -> 'Version':
        """
        Parse a version string into a Version object.
        :param version_str: Version string in the format 'major.minor.patch'.
        :return: Version object.
        """
        parts = version_str.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version string: {version_str}")
        return Version(int(parts[0]), int(parts[1]), int(parts[2]))

    def compare(self, other: 'Version') -> int:
        """
        Compare two versions.
        :param other: Version to compare with.
        :return: 0 if equal, -1 if self < other, 1 if self > other.
        """
        if self.major != other.major:
            return self.major - other.major
        if self.minor != other.minor:
            return self.minor - other.minor
        return self.patch - other.patch

    def as_tuple(self) -> tuple:
        """
        Convert the version to a tuple.
        :return: Tuple of (major, minor, patch).
        """
        return self.major, self.minor, self.patch